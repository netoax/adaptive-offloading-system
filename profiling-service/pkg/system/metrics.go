package system

import (
	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/mem"
)

// Profiler defines an interface to receive system's profiling information
type Profiler interface {
	GetCPU() error
}

// DeviceProfiler ...
type DeviceProfiler struct{}

// NewProfiler ...
func NewProfiler() *DeviceProfiler {
	return &DeviceProfiler{}
}

// GetCPU ...
func (dp *DeviceProfiler) GetCPU() ([]float64, error) {
	cpu, err := cpu.Percent(0, false)
	if err != nil {
		return []float64{}, err
	}

	return cpu, nil
}

// GetMemory ...
func (dp *DeviceProfiler) GetMemory() (float64, error) {
	memory, err := mem.VirtualMemory()
	if err != nil {
		return 0, err
	}

	return memory.UsedPercent, nil
}
