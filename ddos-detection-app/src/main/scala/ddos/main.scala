import ddos.{EntropyDetector, SimpleDetector}

object main {
  def main(args: Array[String]): Unit = {
//    val kind = sys.env("EXECUTION_TYPE")
//    if (kind == "simple") {
      val simpleCep = new SimpleDetector()
      simpleCep.start()
//    } else if (kind == "entropy") {
//      val entropyCep = new EntropyDetector()
//      entropyCep.start()
//    }
  }
}
