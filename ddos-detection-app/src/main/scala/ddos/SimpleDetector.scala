package ddos

import java.util

import ddos.Events.NetworkEvent
import io.circe.{Decoder, parser}
import mqtt.{MqttMessage, MqttSink, MqttSource}
import org.apache.flink.configuration.Configuration
import io.circe.generic.semiauto.deriveDecoder
import org.apache.flink.api.common.ExecutionConfig.GlobalJobParameters
import org.apache.flink.cep.functions.PatternProcessFunction
import org.apache.flink.cep.scala.CEP
import org.apache.flink.cep.scala.pattern.Pattern
import org.apache.flink.streaming.api.scala.{DataStream, StreamExecutionEnvironment, _}
import org.apache.flink.streaming.api.windowing.time.Time
import org.apache.flink.util.Collector

case class ResultEvent(detected: Boolean, address: String)

class SimpleDetector {
  val APPLICATION_DATA_NETWORK_TOPIC = "/cep/application/network/data"
  val APPLICATION_RESPONSE_TOPIC = "/cep/application/response"
  val MQTT_BROKER_HOSTNAME = "localhost"

  def start(): Unit = {
    val conf = new Configuration()
//    conf.setString("rest.port", "8282")
//    conf.setString("taskmanager.memory.task.heap.size", "300")
//    val env = StreamExecutionEnvironment.createLocalEnvironment(4, conf)
//    println(conf)
//    val env = StreamExecutionEnvironment.createLocalEnvironmentWithWebUI(conf)
    val env = StreamExecutionEnvironment.getExecutionEnvironment
//    StreamExecutionEnvironment.cr

    //    env.setStreamTimeCharacteristic(TimeCharacteristic.EventTime)
    env.getConfig.setLatencyTrackingInterval(30000)

    val networkSource: DataStream[MqttMessage] = env
      .addSource(new MqttSource(MQTT_BROKER_HOSTNAME, APPLICATION_DATA_NETWORK_TOPIC))
      .uid("network-data-source")
      .name("mqtt: network-events-data-source")

    // Create NetworkEvent representation
    val mapNetworkData = (data: MqttMessage) => {
      implicit val dataDecoder: Decoder[NetworkEvent] = deriveDecoder[NetworkEvent]
      val d = parser.decode[NetworkEvent](data.getPayload())
      d match {
        case Right(data) => data
        case Left(error) => null
      }
    }

    // Create traffic data stream
    val networkStream: DataStream[NetworkEvent] = networkSource
      .map(mapNetworkData)
      .uid("map-network-event")
      .name("map-network-event")

    // Simple pattern
    val start = Pattern.begin[NetworkEvent]("start")
      .where(e => {
        e.protocol == "tcp"
      })
      .within(Time.seconds(1))
      .times(10)

    val partitionedInput = networkStream.keyBy(event => event.sourceAddr)
    val patternStream = CEP.pattern(partitionedInput, start)

    val patternTestFn = new PatternProcessFunction[NetworkEvent, ResultEvent]() {
      override def processMatch(
                                 map: util.Map[String, util.List[NetworkEvent]],
                                 ctx: PatternProcessFunction.Context,
                                 out: Collector[ResultEvent]): Unit = {
        val event = map.get("start").get(0)
        out.collect(ResultEvent(true, event.sourceAddr))
      }
    }

    val mainResults: DataStream[ResultEvent] = patternStream.process(patternTestFn)
      .name("main-results-collecting")
      .uid("main-results-collecting")

    mainResults
      .addSink(new MqttSink[ResultEvent](MQTT_BROKER_HOSTNAME, APPLICATION_RESPONSE_TOPIC))
      .name("mqtt: network-event-response-sink")
      .uid("network-event-response-sink")

    env.execute("DDoS Attack Detection")
  }
}
