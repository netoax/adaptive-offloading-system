package ddos

import java.util

import ddos.Events.NetworkEvent
import io.circe.{Decoder, parser}
import mqtt.{MqttMessage, MqttSink, MqttSource}
import org.apache.flink.configuration.Configuration
import io.circe.generic.semiauto.deriveDecoder
import org.apache.flink.api.common.ExecutionConfig.GlobalJobParameters
import org.apache.flink.api.common.state.ValueState
import org.apache.flink.cep.functions.PatternProcessFunction
import org.apache.flink.cep.scala.CEP
import org.apache.flink.cep.scala.pattern.Pattern
import org.apache.flink.streaming.api.scala.{DataStream, StreamExecutionEnvironment, _}
import org.apache.flink.streaming.api.windowing.time.Time
import org.apache.flink.util.Collector

class EntropyDetector {
  val APPLICATION_DATA_NETWORK_TOPIC = "/cep/application/network/data"
  val APPLICATION_RESPONSE_TOPIC = "/cep/application/response"
  val MQTT_BROKER_HOSTNAME = "localhost"

//  var numberOfEvents = 0
//  var calculatedEntropy: Double = 0.0

  var sum: ValueState[Double] = _

  def start(): Unit = {
    val conf = new Configuration()
//    conf.setString("rest.port", "8282")
//    conf.setString("taskmanager.memory.task.heap.size", "300")
//    val env = StreamExecutionEnvironment.createLocalEnvironment(4, conf)
//    println(conf)
    val env = StreamExecutionEnvironment.createLocalEnvironmentWithWebUI(conf)
//    val env = StreamExecutionEnvironment.getExecutionEnvironment
//    StreamExecutionEnvironment.cr

//    env.getConfig.setGlobalJobParameters()

    //    env.setStreamTimeCharacteristic(TimeCharacteristic.EventTime)
    env.getConfig.setLatencyTrackingInterval(30000)



    val networkSource: DataStream[MqttMessage] = env
      .addSource(new MqttSource(MQTT_BROKER_HOSTNAME, APPLICATION_DATA_NETWORK_TOPIC))
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
      .name("map-network-event")

//    // Simple pattern
//    val start = Pattern.begin[NetworkEvent]("start")
//      .where(e => {
//        e.protocol == "tcp"
//      })
//      .within(Time.seconds(1))
//      .times(10)

    val cnts: DataStream[Int] = networkStream
      .map(_ => 1)                    // convert to 1
      .timeWindowAll(Time.seconds(5)) // group into 5 second windows
      .reduce( (x, y) => x + y)
      .map(windowCount => {
        var numberOfEvents = 0.0
        var calculatedEntropy = 0.0

        val lnOf2 = scala.math.log(2) // natural log of 2
        def log2(x: Double): Double = scala.math.log(x) / lnOf2

        sum.update(sum.value() + windowCount)
        val divisor = windowCount / numberOfEvents
        println("divisor (log): " + log2(divisor))
        calculatedEntropy = divisor * (math.log10(divisor) / math.log10(divisor))
        println("entropy: " + calculatedEntropy)
        windowCount
      })
      .name("count records in time window")// sum 1s to count


//    cnts
//      .map((windowCount) => {
//        numberOfEvents = numberOfEvents + windowCount
//        val divisor = windowCount / numberOfEvents
//        calculatedEntropy = divisor * (math.log10(divisor) / math.log10(divisor))
//        print(calculatedEntropy)
//        windowCount
//      })
//      .name("calculate-entropy-event")

//    val partitionedInput = networkStream.keyBy(event => event.sourceAddr)
//    val patternStream = CEP.pattern(partitionedInput, start)
//    val patternTestFn = new PatternProcessFunction[NetworkEvent, ResultEvent]() {
//      override def processMatch(
//                                 map: util.Map[String, util.List[NetworkEvent]],
//                                 ctx: PatternProcessFunction.Context,
//                                 out: Collector[ResultEvent]): Unit = {
//        val event = map.get("start").get(0)
//        out.collect(ResultEvent(true, event.sourceAddr))
//      }
//    }

//    val mainResults: DataStream[ResultEvent] = cnts.process(patternTestFn)
//      .name("main-results-collecting")

    cnts
      .addSink(new MqttSink[Int](MQTT_BROKER_HOSTNAME, APPLICATION_RESPONSE_TOPIC))
      .name("mqtt: network-event-count-sink")

    env.execute("DDoS Attack Detection")
  }
}
