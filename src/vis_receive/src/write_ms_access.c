#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include <oskar_measurement_set.h>
#include "buffer.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846264338327950288
#endif

//*************************************************
//* Open existing MS
//* Return 0 if error 
//*************************************************


oskar_MeasurementSet* open_ms(const char* file_name)
{
    printf("Opening Measurement Set: %s\n", file_name);
    oskar_MeasurementSet* ms = oskar_ms_open(file_name);
    return ms;
}

//*************************************************
//* Create new MS
//* Return 0 if error 
//*************************************************

oskar_MeasurementSet* create_ms(
        const char* oms_file_name, const char* app_name,
        unsigned int num_stations, unsigned int num_channels,
        unsigned int num_pols, double ref_freq_hz,
        double freq_inc_hz, int write_autocorr, int write_crosscorr)
{
    oskar_MeasurementSet* ms = oskar_ms_create(
            oms_file_name, app_name,
            num_stations, num_channels,
            num_pols, ref_freq_hz,
            freq_inc_hz, write_autocorr,
            write_crosscorr);
    return ms;
}


int write_ms(oskar_MeasurementSet* ms, int buf_index, int num_pols,
             int num_channels, int num_times,int num_baselines,
             struct DataType* vis_data)
{
    /* Define data dimensions. */
    int num_stations = 3;
    int t, b, c, p, rows;
    double ref_freq_hz = 100e6;
    double freq_inc_hz = 100e3;
    double exposure_sec = 1.0;
    double interval_sec = 1.0;
    struct DataType* vis2 = malloc(num_times * num_channels *
                                   num_baselines * num_pols *
                                   2 * sizeof(float));

    /* Data to write are stored in these arrays. */
    double* uu = (double*) calloc(num_baselines, sizeof(double));
    double* vv = (double*) calloc(num_baselines, sizeof(double));
    double* ww = (double*) calloc(num_baselines, sizeof(double));
    float* vis = (float*) calloc(
            num_times * num_channels * num_baselines * num_pols,
            2 * sizeof(float));


    /* Set phase centre. */
    const double ra_rad = M_PI / 4;
    const double dec_rad = -M_PI / 4;
    oskar_ms_set_phase_centre(ms, 0, ra_rad, dec_rad);
    rows = oskar_ms_num_rows(ms);

    /* Write data one block at a time. */
    for (t = 0; t < num_times; ++t)
    {
        /* Dummy data to write. */
        const double time_stamp = 51544.5 * 86400.0 + (double)t;
        const unsigned int start_row = t * num_baselines;
        const unsigned int base_row = buf_index * num_times * num_baselines;
        const size_t vis_block_start =
                2 * num_pols * num_baselines * num_channels * t;
//                num_baselines * num_channels * t;

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
        oskar_ms_write_coords_d(ms, base_row+start_row, num_baselines, uu, vv, ww,
                                exposure_sec, interval_sec, time_stamp);
        vis2 = vis_data;
        printf("vis2-> %d %d %d %p\n", base_row+start_row, num_channels, num_baselines, &((vis2->vis+vis_block_start)->x));
        oskar_ms_write_vis_f(ms, base_row+start_row, 0, num_channels, num_baselines,
                             &((vis2->vis + vis_block_start)->x));
//                &((vis2->vis)->x));
    }

    /* Clean up. */
    free(uu);
    free(vv);
    free(ww);
    free(vis);
    return 0;
}

void close_ms(oskar_MeasurementSet* ms)
{
    oskar_ms_close(ms);
}
