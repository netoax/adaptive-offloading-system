package ddos

object Events {

  case class NetworkEvent(pkSeqID: Int,
                          timestamp: Double,
                          protocol: String,
                          sourceAddr: String,
                          sourcePort: Int,
                          destAddr: String,
                          destPort: Int,
                          bytes: Int,
                          state: String
                         )

}
