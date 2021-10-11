package ddos

import java.util

import ddos.Events.NetworkEvent
import io.circe.{Decoder, parser}
import mqtt.{MqttMessage, MqttSink, MqttSource}
import org.apache.flink.configuration.Configuration
import io.circe.generic.semiauto.deriveDecoder
import org.apache.flink.api.common.ExecutionConfig.GlobalJobParameters
import org.apache.flink.cep.functions.PatternProcessFunction
import org.apache.flink.cep.nfa.aftermatch.AfterMatchSkipStrategy
import org.apache.flink.cep.scala.CEP
import org.apache.flink.cep.scala.pattern.Pattern
import org.apache.flink.streaming.api.TimeCharacteristic
import org.apache.flink.streaming.api.scala.{DataStream, StreamExecutionEnvironment, _}
import org.apache.flink.streaming.api.windowing.time.Time
import org.apache.flink.util.Collector

case class ResultEvent(detected: Boolean, address: String)

class SimpleDetector {
  val APPLICATION_DATA_NETWORK_TOPIC = "/cep/application/network/data"
  val APPLICATION_RESPONSE_TOPIC = "/cep/application/response"
  val MQTT_BROKER_HOSTNAME = "localhost"
  val LATENCY_INTERVAL_MS = 30000
  val DEFAULT_WINDOW_TIME_S = 1
  val DEFAULT_MATCH_TIMES = 128

  def start(mode: String): Unit = {
    var env = StreamExecutionEnvironment.getExecutionEnvironment

    if (mode == "edge") {
      val conf = new Configuration()
      conf.setString("rest.port", "8282")
        env = StreamExecutionEnvironment.createLocalEnvironmentWithWebUI(conf)
    }

    env.getConfig.setLatencyTrackingInterval(LATENCY_INTERVAL_MS)
//    env.setStreamTimeCharacteristic(TimeCharacteristic.EventTime)

    var windowSeconds = 1
    var matchTimes = 128

    if (mode == "edge") {
      windowSeconds = sys.env("WINDOW_SECONDS") match {
        case "" => DEFAULT_WINDOW_TIME_S
        case s => s.toInt
      }

      matchTimes = sys.env("MATCH_TIMES") match {
        case "" => DEFAULT_MATCH_TIMES
        case s => s.toInt
      }
    }


    val networkSource: DataStream[MqttMessage] = env
      .addSource(new MqttSource(MQTT_BROKER_HOSTNAME, APPLICATION_DATA_NETWORK_TOPIC))
      .uid("network-data-source")
      .name("mqtt: network-events-data-source")

    val filterNetworkData = (data: MqttMessage) => {
      implicit val dataDecoder: Decoder[NetworkEvent] = deriveDecoder[NetworkEvent]
      val future = parser.decode[NetworkEvent](data.getPayload())
      future match {
        case Right(data) => {
          true
        }
        case Left(error) => {
          false
        }
      }
    }

    // Create NetworkEvent representation
    val mapNetworkData = (data: MqttMessage) => {
      implicit val dataDecoder: Decoder[NetworkEvent] = deriveDecoder[NetworkEvent]
      val future = parser.decode[NetworkEvent](data.getPayload())
      future match {
        case Right(data) => {
          data
        }
        case Left(error) => {
//          println(error)
          null
        }
      }
    }

    // Create traffic data stream
    val networkStream: DataStream[NetworkEvent] = networkSource
      .filter(filterNetworkData)
      .map(mapNetworkData)
      .uid("map-network-event")
      .name("map-network-event")


    val edgePattern = Pattern.begin[NetworkEvent]("start", AfterMatchSkipStrategy.skipToNext())
      .where(_.protocol == "tcp")
      .within(Time.seconds(windowSeconds))
      .times(matchTimes)

    val cloudPattern = Pattern.begin[NetworkEvent]("start", AfterMatchSkipStrategy.skipToNext())
      .where(_.protocol == "tcp")
      .within(Time.seconds(DEFAULT_WINDOW_TIME_S))
      .times(DEFAULT_MATCH_TIMES)

    val startPattern = mode match {
      case "edge" => edgePattern
      case "cloud" => cloudPattern
    }

    val partitionedInput = networkStream.keyBy(event => event.sourceAddr)
    val patternStream = CEP.pattern(partitionedInput, startPattern)

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
