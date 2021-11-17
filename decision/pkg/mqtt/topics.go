package mqtt

var (
	// offloading control
	offloadingSignal          = "/prediction/offloading"
	offloadingRequest         = "/offloading/request"
	offloadingAllowed         = "/offloading/request/allowed"
	offloadingStateSubmission = "/offloading/state/submission"
	offloadingStateConfirmed  = "/offloading/state/confirmed"
	offloadingStopRequest     = "/offloading/stop/request"
	offloadingStopConfirmed   = "/offloading/stop/confirmed"
	offloadingEdgeRestarted   = "/offloading/edge/restarted"

	// contextual data
	policyStatusUpdate     = "/policies/status"
	conceptDriftOccurrence = "/prediction/drift"
	profilingMetrics       = "/profiling/metrics"

	// application
	dataSent        = "/application/+/data"
	applicationName = "/application/name"
	remoteResponse  = "/cep/application/response"
	// dataToCep = "/cep/application/+/data"
)
