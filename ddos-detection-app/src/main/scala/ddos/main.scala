import ddos.{EntropyDetector, SimpleDetector}
import org.apache.flink.api.java.utils.ParameterTool

object main {
  def main(args: Array[String]): Unit = {
    val parameter = ParameterTool.fromArgs(args)
    val mode = parameter.get("mode", "edge")
//    if (kind == "simple") {
      val simpleCep = new SimpleDetector()
      println("mode: " + mode)
      simpleCep.start(mode)
//    } else if (kind == "entropy") {
//      val entropyCep = new EntropyDetector()
//      entropyCep.start()
//    }
  }
}
