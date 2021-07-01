import ddos.Detector

object main {
  def main(args: Array[String]): Unit = {
    val cep = new Detector()
    cep.start()
  }
}
