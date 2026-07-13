module axis_bcd #(
    parameter c_INPUT_DATA_WIDTH = 16,
    parameter c_OUTPUT_DATA_WIDTH = c_INPUT_DATA_WIDTH + 4*(c_INPUT_DATA_WIDTH + 3 - 1)/3 
) (
    input wire i_clk,
    input wire i_rst,

    input wire [c_INPUT_DATA_WIDTH - 1:0] s_axis_tdata,
	input wire s_axis_tvalid,
	output wire s_axis_tready,
	
	output wire [c_OUTPUT_DATA_WIDTH - 1:0] m_axis_tdata,
	output wire m_axis_tvalid,
	input wire m_axis_tready
);

reg [c_INPUT_DATA_WIDTH - 1:0] s_axis_tdata_reg = {c_INPUT_DATA_WIDTH{1'b0}};
reg s_axis_tready_reg = 1'b1;

assign s_axis_tready = s_axis_tready_reg;

reg [c_OUTPUT_DATA_WIDTH - 1:0] m_axis_tdata_reg = {c_OUTPUT_DATA_WIDTH{1'b0}};
reg m_axis_tvalid_reg = 1'b0;

assign m_axis_tdata = m_axis_tdata_reg;
assign m_axis_tvalid = m_axis_tvalid_reg;

localparam c_COUNT_WIDTH = $clog2(c_INPUT_DATA_WIDTH);
localparam c_NO_DIGITS = c_OUTPUT_DATA_WIDTH/4;
localparam c_DIGIT_COUNT_WIDTH = $clog2(c_NO_DIGITS);

reg [c_COUNT_WIDTH - 1:0] r_count = {c_INPUT_DATA_WIDTH{1'b0}};
reg [c_DIGIT_COUNT_WIDTH - 1:0] r_digit_count = {c_DIGIT_COUNT_WIDTH{1'b0}};

localparam s_IDLE = 2'd0;
localparam s_SHIFT = 2'd1;
localparam s_CHECK = 2'd2;
localparam s_DONE = 3'd3;

reg [1:0] r_state = s_IDLE;

always @(posedge i_clk) begin
	case (r_state)
		s_IDLE: begin
			if (s_axis_tvalid && s_axis_tready) begin
				s_axis_tdata_reg <= s_axis_tdata;
				s_axis_tready_reg <= 1'b0;
				m_axis_tdata_reg <= {c_OUTPUT_DATA_WIDTH{1'b0}};
				r_count <= {c_INPUT_DATA_WIDTH{1'b0}};
				r_digit_count  <= {c_DIGIT_COUNT_WIDTH{1'b0}};
				r_state <= s_SHIFT;
			end
		end

		s_SHIFT: begin
			r_count <= r_count + 1'b1;
			s_axis_tdata_reg <= s_axis_tdata_reg << 1'b1;
			m_axis_tdata_reg <= m_axis_tdata_reg << 1'b1;
			m_axis_tdata_reg[0] <= s_axis_tdata_reg[c_INPUT_DATA_WIDTH - 1];
			r_digit_count <= {c_DIGIT_COUNT_WIDTH{1'b0}};
			r_state <= s_CHECK;
			if (r_count == c_INPUT_DATA_WIDTH - 1'b1) begin
				m_axis_tvalid_reg <= 1'b1;
				r_state <= s_DONE;
			end
		end

		s_CHECK: begin
			r_digit_count <= r_digit_count + 1'b1;
			if (m_axis_tdata_reg[4*r_digit_count +:4] >= 3'd5) begin
				m_axis_tdata_reg[4*r_digit_count +:4] <= m_axis_tdata_reg[4*r_digit_count +:4] + 2'd3;
			end

			if (r_digit_count == c_NO_DIGITS - 1'b1) begin
				r_state <= s_SHIFT;
			end
		end

		s_DONE: begin
			if (m_axis_tvalid && m_axis_tready) begin
				s_axis_tready_reg <= 1'b1;
				m_axis_tvalid_reg <= 1'b0;
				r_state <= s_IDLE;
			end
		end
	endcase
end

endmodule
