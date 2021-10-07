package runner

type OverallContext struct {
	State      string `json:"state"`
	Violated   bool   `json:"violated"`
	Fallback   bool   `json:"fallback"`
	BufferSize int    `json:"bufferSize"`
	Timestamp  string `json:"timestamp"`
}
