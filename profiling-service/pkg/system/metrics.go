package system

import (
	"errors"

	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/mem"
	"github.com/shirou/gopsutil/v3/net"
)

// Profiler defines an interface to receive system's profiling information
type Profiler interface {
	GetCPU() error
}

// DeviceProfiler ...
type DeviceProfiler struct {
	bandwidthValue uint64
}

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

func (dp *DeviceProfiler) getNetworkStatsByInterface(name string) (*net.IOCountersStat, error) {
	counters, err := net.IOCounters(true)
	if err != nil {
		return nil, err
	}

	for _, c := range counters {
		if c.Name == name {
			return &c, nil
		}
	}

	return nil, errors.New("interface stats not found")
}
