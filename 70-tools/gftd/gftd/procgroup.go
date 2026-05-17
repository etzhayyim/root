package main

import (
	"os"
	"os/exec"
	"os/signal"
	"sync"
	"syscall"
)

// childPIDs tracks all child process PIDs for cleanup on gftd exit.
var (
	childPIDs   []int
	childPIDsMu sync.Mutex
)

func init() {
	// On SIGINT/SIGTERM/SIGKILL(parent), kill all tracked child process groups.
	c := make(chan os.Signal, 1)
	signal.Notify(c, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-c
		killAllChildren()
		os.Exit(1)
	}()
}

// setProcGroup configures cmd to run in its own process group so we can
// kill the entire tree (cmd + all descendants) on cleanup.
func setProcGroup(cmd *exec.Cmd) {
	cmd.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
}

// trackChild records a started process for cleanup.
func trackChild(cmd *exec.Cmd) {
	if cmd.Process == nil {
		return
	}
	childPIDsMu.Lock()
	childPIDs = append(childPIDs, cmd.Process.Pid)
	childPIDsMu.Unlock()
}

// untrackChild removes a finished process from the cleanup list.
func untrackChild(cmd *exec.Cmd) {
	if cmd.Process == nil {
		return
	}
	pid := cmd.Process.Pid
	childPIDsMu.Lock()
	for i, p := range childPIDs {
		if p == pid {
			childPIDs = append(childPIDs[:i], childPIDs[i+1:]...)
			break
		}
	}
	childPIDsMu.Unlock()
}

// killAllChildren sends SIGKILL to all tracked child process groups.
func killAllChildren() {
	childPIDsMu.Lock()
	pids := make([]int, len(childPIDs))
	copy(pids, childPIDs)
	childPIDsMu.Unlock()

	for _, pid := range pids {
		// Kill the entire process group (negative PID)
		syscall.Kill(-pid, syscall.SIGKILL)
	}
}
