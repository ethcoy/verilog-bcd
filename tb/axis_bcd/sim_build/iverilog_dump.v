module iverilog_dump();
initial begin
    $dumpfile("axis_bcd.fst");
    $dumpvars(0, axis_bcd);
end
endmodule
