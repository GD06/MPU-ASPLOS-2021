#!/usr/bin/env python3 

import unittest 
import numpy as np
import struct
import os
import tempfile
import subprocess 

from backend.branch_analysis import reconvergence_analysis 
import program.prog_api as prog_api 
import config.config_api as config_api 
import simulator.sim_api as sim_api 

NUM_THREADS = 128


def _relayout_matrix(input_matrix, num_rows, num_cols):
    output_matrix = np.zeros((num_rows, num_cols))
    for i in range(num_rows):
        for j in range(0, num_cols, NUM_THREADS):
            for k in range(NUM_THREADS):
                output_matrix[i, j + k] = input_matrix.flat[
                    (j // NUM_THREADS) * NUM_THREADS * num_rows 
                    + i * NUM_THREADS + k]

    return output_matrix.astype(np.float32)


class TestGEMV(unittest.TestCase): 

    def setUp(self):
        self.curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.proj_dir = os.path.dirname(os.path.dirname(self.curr_dir))
        _, self.ptx_file = tempfile.mkstemp(suffix=".ptx", dir=self.curr_dir)

        cuda_file_path = os.path.join(
            self.proj_dir, "benchmark", "gemv", "gemv_kernel.cu"
        )
        self.assertTrue(os.path.isfile(cuda_file_path))
        self.assertTrue(os.path.isfile(self.ptx_file))

        subprocess.run(
            ["nvcc", "-O2", "--ptx", "-o", self.ptx_file, cuda_file_path], 
            check=True
        )

        self.raw_kernel_list = prog_api.load_kernel(self.ptx_file)
        self.kernel_list = []
        for each_kernel in self.raw_kernel_list:
            output_kernel = reconvergence_analysis(each_kernel, mode="instr")
            self.kernel_list.append(output_kernel)
        self.config = config_api.load_hardware_config() 
        return 

    def tearDown(self):
        os.remove(self.ptx_file)

    def _run_gemv(self, num_rows, num_cols, grid_dim, block_dim, mapping_dict):
        self.assertTupleEqual(block_dim, (1, 1, NUM_THREADS))

        hardware = sim_api.init_hardware(self.config)
        ptr_matrix = hardware.mem.allocate(num_rows * num_cols * 4)
        ptr_invec = hardware.mem.allocate(num_cols * 4)
        ptr_outvec = hardware.mem.allocate(num_rows * 4)
        hardware.mem.finalize() 

        input_matrix = np.random.rand(num_rows * num_cols).astype(np.float32)
        input_vector = np.random.rand(num_cols).astype(np.float32)
        hardware.mem.set_value(ptr_matrix, input_matrix.tobytes())
        hardware.mem.set_value(ptr_invec, input_vector.tobytes())

        total_cycles, sim_freq = hardware.run_simulation(
            kernel=self.kernel_list[0],
            kernel_args=[ptr_matrix, ptr_invec, ptr_outvec, 
                         num_rows, num_cols],
            grid_dim=grid_dim,
            block_dim=block_dim,
            block_schedule=mapping_dict,
        )

        output_buffer = hardware.mem.get_value(ptr_outvec, num_rows * 4)
        sim_results = np.array(
            struct.unpack("{}f".format(num_rows), output_buffer)
        ).astype(np.float32)

        tmp_matrix = _relayout_matrix(input_matrix, num_rows, num_cols)
        groud_truth = tmp_matrix.dot(input_vector)

        np.testing.assert_allclose(sim_results, groud_truth, atol=1e-3)
        return 

    def test_single_threadblock(self):
        self._run_gemv(
            num_rows=1,
            num_cols=256,
            grid_dim=(1, 1, 1),
            block_dim=(1, 1, 128),
            mapping_dict={0: 0},
        )
        return
    
    def test_multiple_matrix_blocks(self):
        self._run_gemv(
            num_rows=10,
            num_cols=128,
            grid_dim=(1, 1, 3),
            block_dim=(1, 1, 128),
            mapping_dict={0: 0, 1: 1, 2: 2},
        )
        return 


if __name__ == "__main__":
    unittest.main() 
