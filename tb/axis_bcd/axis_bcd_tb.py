import cocotb

import os
import random

from cocotb import simulator
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Edge, Event, Timer
from cocotb.queue import AbstractQueue, Queue
from cocotb.simtime import get_sim_time

from cocotb_test.simulator import run

class axis_source:
    def __init__(self, s_clk, s_axis_tdata, s_axis_tvalid, s_axis_tready, s_axis_tlast=None):
        self.s_clk = s_clk
        self.s_axis_tdata = s_axis_tdata
        self.s_axis_tvalid = s_axis_tvalid
        self.s_axis_tready = s_axis_tready
        self.s_axis_tlast = s_axis_tlast
        self.s_axis_tdata_sent = []
        self.queue = Queue()
        self.last = Queue()
        self.data_present = Event()
        cocotb.start_soon(self.__axis_source__())
    def send_nowait(self, data):
        for i in range(len(data)):
            self.queue.put_nowait(data[i])
            if (i == len(data) - 1):
                self.last.put_nowait(1)
            else:
                self.last.put_nowait(0)
        self.data_present.set()
    async def __axis_source__(self):
        while (True):
            await self.data_present.wait()
            while (not self.queue.empty()):
                self.s_axis_tdata.value = self.queue.get_nowait()
                if (self.s_axis_tvalid != None):
                    self.s_axis_tvalid.value = 1
                last_indicator = self.last.get_nowait()
                if (self.s_axis_tlast != None):
                    if (last_indicator == 1):
                        self.s_axis_tlast.value = 1
                    else:
                        self.s_axis_tlast.value = 0
                await RisingEdge(self.s_clk)
                while (not self.s_axis_tready.value):
                    await RisingEdge(self.s_clk)
                self.s_axis_tdata_sent.append(self.s_axis_tdata.value)
            self.data_present.clear()
            if (self.s_axis_tvalid != None):
                self.s_axis_tvalid.value = 0
            if (self.s_axis_tlast != None):
                self.s_axis_tlast.value = 0

class axis_sink:
    def __init__(self, m_clk, m_axis_tdata, m_axis_tvalid, m_axis_tready):
        self.m_clk = m_clk
        self.m_axis_tdata = m_axis_tdata
        self.m_axis_tvalid = m_axis_tvalid
        self.m_axis_tready = m_axis_tready
        self.m_axis_tdata_read = []
        cocotb.start_soon(self.__axis_sink__())
    async def __axis_sink__(self):
        while (True):
            await RisingEdge(self.m_clk)
            if (not self.m_axis_tvalid.value):
                await RisingEdge(self.m_axis_tvalid)
            if (self.m_axis_tready != None):
                self.m_axis_tready.value = 1
            await RisingEdge(self.m_clk)
            while (self.m_axis_tvalid.value):
                self.m_axis_tdata_read.append(self.m_axis_tdata.value)
                await RisingEdge(self.m_clk)
            if (self.m_axis_tready != None):
                self.m_axis_tready.value = 0

@cocotb.test()
async def axis_bcd(dut):
    dut.i_rst.value = 0
    dut.i_clk.value = 0

    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())

    await RisingEdge(dut.i_clk)

    src = axis_source(dut.i_clk, dut.s_axis_tdata, dut.s_axis_tvalid, dut.s_axis_tready)
    snk = axis_sink(dut.i_clk, dut.m_axis_tdata, dut.m_axis_tvalid, dut.m_axis_tready)

    l = 500
    data = []
    for i in range(l):
        data.append(i)

    src.send_nowait(data)

    for i in range(l):
        await RisingEdge(dut.m_axis_tvalid)

    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    data_sent = [int(x) for x in src.s_axis_tdata_sent]
    data_read = [int(hex(x)[2:]) for x in snk.m_axis_tdata_read]
    print(data_sent)
    print()
    print(data_read)

    assert data_sent == data_read, 'Double-dabble did not work...'

parameters = {}
parameters['c_INPUT_DATA_WIDTH'] = 16

c_INPUT_DATA_WIDTH = parameters['c_INPUT_DATA_WIDTH']

if __name__ == "__main__":
    run(verilog_sources = [
            './../../rtl/axis_bcd.v',
        ],
        toplevel = "axis_bcd",
        module = "axis_bcd_tb",
        parameters = parameters,
        sim_build = "sim_build/",
        timescale = "1ns/1ps",
        force_compile = True,
        seed = int(0),
        waves = 1,
    )