name := "ddos-detection-app"

version := "0.1"

scalaVersion := "2.11.11"

//javaHome := Some(file("/Library/Java/JavaVirtualMachines/jdk-13.0.1.jdk/Contents/Home"))

// https://mvnrepository.com/artifact/org.apache.flink/flink-scala
libraryDependencies += "org.apache.flink" %% "flink-scala" % "1.10.0"

// https://mvnrepository.com/artifact/org.apache.flink/flink-cep-scala
libraryDependencies += "org.apache.flink" %% "flink-cep-scala" % "1.10.0"

// https://mvnrepository.com/artifact/org.apache.flink/flink-streaming-scala
libraryDependencies += "org.apache.flink" %% "flink-streaming-scala" % "1.10.0"

// https://mvnrepository.com/artifact/org.apache.flink/flink-connector-kafka
libraryDependencies += "org.apache.flink" %% "flink-connector-kafka" % "1.10.0"

// https://mvnrepository.com/artifact/org.apache.flink/flink-connector-rabbitmq
libraryDependencies += "org.apache.flink" %% "flink-connector-rabbitmq" % "1.10.0"

// https://mvnrepository.com/artifact/org.apache.flink/flink-state-processor-api
libraryDependencies += "org.apache.flink" %% "flink-state-processor-api" % "1.10.0"

libraryDependencies += "org.apache.flink" %% "flink-runtime-web" % "1.10.0"

libraryDependencies += "org.fusesource.mqtt-client" % "mqtt-client" % "1.16"

libraryDependencies += "com.google.code.gson" % "gson" % "2.8.9"


val circeVersion = "0.7.0"
libraryDependencies ++= Seq(
  "io.circe"  %% "circe-core"     % circeVersion,
  "io.circe"  %% "circe-generic"  % circeVersion,
  "io.circe"  %% "circe-parser"   % circeVersion
)
