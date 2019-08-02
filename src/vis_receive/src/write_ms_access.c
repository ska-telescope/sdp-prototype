#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include <oskar_measurement_set.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846264338327950288
#endif

int write_ms(const char* file_name,int num_pols, int num_channels, int num_times,int num_baselines)
{
    /* Define data dimensions. */
//    int num_pols = 4;
//    int num_channels = 2;
    int num_stations = 3;
//    int num_times = 4;
//    int num_baselines = num_stations * (num_stations - 1) / 2;
    int t, b, c, p;
    double ref_freq_hz = 100e6;
    double freq_inc_hz = 100e3;
    double exposure_sec = 1.0;
    double interval_sec = 1.0;
		oskar_MeasurementSet* ms;

    /* Data to write are stored in these arrays. */
    double* uu = (double*) calloc(num_baselines, sizeof(double));
    double* vv = (double*) calloc(num_baselines, sizeof(double));
    double* ww = (double*) calloc(num_baselines, sizeof(double));
    float* vis = (float*) calloc(
            num_times * num_channels * num_baselines * num_pols,
            2 * sizeof(float));
		ms = oskar_ms_open(file_name);
    /* Create the empty Measurement Set if it doesn't exist. */
		if( ms == 0)
	    ms = oskar_ms_create(file_name, "C test main",
  	          num_stations, num_channels, num_pols, ref_freq_hz, freq_inc_hz,
    	        0, 1);
		

    /* Set phase centre. */
    const double ra_rad = M_PI / 4;
    const double dec_rad = -M_PI / 4;
    oskar_ms_set_phase_centre(ms, 0, ra_rad, dec_rad);

    /* Write data one block at a time. */
    for (t = 0; t < num_times; ++t)
    {
        /* Dummy data to write. */
        const double time_stamp = 51544.5 * 86400.0 + (double)t;
        for (b = 0; b < num_baselines; ++b)
        {
            uu[b] = t + 1;
            vv[b] = t * 10 + 2;
            ww[b] = t * 100 + 3;
        }
        for (c = 0; c < num_channels; ++c)
        {
            for (b = 0; b < num_baselines; ++b)
            {
                for (p = 0; p < num_pols; ++p)
                {
                    const size_t index = 2 * (num_pols * (num_baselines *
                            (num_channels * t + c) + b) + p);
                    vis[index + 0] = t * 10 + b;
                    vis[index + 1] = c + 1;
                }
            }
        }

        /* Write coordinates and visibilities. */
        const unsigned int start_row = t * num_baselines;
        const size_t vis_block_start =
                2 * num_pols * num_baselines * num_channels * t;
        oskar_ms_write_coords_d(ms, start_row, num_baselines, uu, vv, ww,
                exposure_sec, interval_sec, time_stamp);
        oskar_ms_write_vis_f(ms, start_row, 0, num_channels, num_baselines,
                vis + vis_block_start);
    }

    /* Clean up. */
    oskar_ms_close(ms);
    free(uu);
    free(vv);
    free(ww);
    free(vis);
    return 0;
}

