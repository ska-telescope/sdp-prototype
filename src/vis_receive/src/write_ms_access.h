#include <oskar_measurement_set.h>

#ifdef __cplusplus
extern "C"{
#endif

oskar_MeasurementSet* open_ms(const char* file_name);
oskar_MeasurementSet* create_ms(const char* oms_file_name, const char* app_name,
  	          unsigned int num_stations, unsigned int num_channels,
							unsigned int num_pols, double ref_freq_hz,
							double freq_inc_hz, int write_autocorr, int write_crosscorr);
int write_ms(oskar_MeasurementSet* ms, int index, int num_pols,
        int num_channels, int num_times,int num_baselines, struct DataType **vis_data);
void close_ms(oskar_MeasurementSet* ms);

#ifdef __cplusplus
}
#endif
