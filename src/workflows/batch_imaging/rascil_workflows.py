"""
Interfaces to RASCIL workflows.
"""

import logging
import numpy

from astropy.coordinates import SkyCoord
from astropy import units as u

from rascil.data_models import PolarisationFrame
from rascil.processing_components import (
    create_low_test_image_from_gleam, export_blockvisibility_to_ms,
    create_blockvisibility_from_ms, create_image_from_visibility,
    create_calibration_controls, export_image_to_fits
)
from rascil.workflows import (
    predict_list_rsexecute_workflow, simulate_list_rsexecute_workflow,
    corrupt_list_rsexecute_workflow, ical_list_rsexecute_workflow
)
from rascil.workflows.rsexecute.execution_support.rsexecute import rsexecute

# Parameters used by workflows....
#
# freq_min: minimum frequency (Hz)
# freq_max: maximum frequency (Hz)
# nfreqwin: number of frequency windows
# ntimes: number of time samples
# rmax: maximum radius from centre of array (metres)
# ra: right ascension (degrees)
# dec: declination (degrees)
# buffer_vis: buffer for visibilities
# buffer_img: buffer for images

def init_logging():
    """Initialise logging."""
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%DT%H:%M:%S',
        level=logging.INFO
    )


def set_client(client):
    """Set RASCIL Dask client.

    :param client: Dask distributed client

    """
    rsexecute.set_client(client=client, dask=True)


def close_client():
    """Close RASCIL Dask client.

    """
    rsexecute.close()


def simulate(parameters):
    """Simulate visibility data.

    :param parameters: pipeline parameters (dict)

    """
    # Get parameters, setting default value if not present
    freq_min = parameters.get('freq_min', 0.9e8)
    freq_max = parameters.get('freq_max', 1.1e8)
    nfreqwin = parameters.get('nfreqwin', 8)
    ntimes = parameters.get('ntimes', 5)
    rmax = parameters.get('rmax', 750.0)
    ra = parameters.get('ra', 0.0)
    dec = parameters.get('dec', -30.0)
    dir_vis = '/buffer/' + parameters.get('buffer_vis')

    frequency = numpy.linspace(freq_min, freq_max, nfreqwin)
    channel_bandwidth = numpy.array(nfreqwin * [frequency[1] - frequency[0]])
    times = numpy.linspace(-numpy.pi / 6.0, numpy.pi / 6.0, ntimes)
    phasecentre = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame='icrs', equinox='J2000')

    npixel = 1024
    cellsize = 0.0005

    rsexecute.run(init_logging)

    vis_list = simulate_list_rsexecute_workflow(
        'LOWBD2',
        rmax=rmax,
        frequency=frequency,
        channel_bandwidth=channel_bandwidth,
        times=times,
        phasecentre=phasecentre,
        order='frequency',
        format='blockvis'
    )
    vis_list = rsexecute.persist(vis_list)

    model_list = [
        rsexecute.execute(create_low_test_image_from_gleam)(
            npixel=npixel,
            frequency=[frequency[f]],
            channel_bandwidth=[channel_bandwidth[f]],
            cellsize=cellsize,
            phasecentre=phasecentre,
            polarisation_frame=PolarisationFrame('stokesI'),
            flux_limit=3.0,
            applybeam=True
        )
        for f in range(nfreqwin)
    ]

    def print_max(v):
        print(numpy.max(numpy.abs(v.vis)))
        return v

    imaging_context = 'ng'
    vis_slices = 1
    print('Using {}'.format(imaging_context))

    predicted_vislist = predict_list_rsexecute_workflow(
        vis_list, model_list, context=imaging_context,
        vis_slices=vis_slices, verbosity=2
    )
    corrupted_vislist = corrupt_list_rsexecute_workflow(
        predicted_vislist, phase_error=1.0, seed=180555
    )
    corrupted_vislist = [
        rsexecute.execute(print_max)(v) for v in corrupted_vislist
    ]
    export_list = [
        rsexecute.execute(export_blockvisibility_to_ms)(
            '{}/ska_pipeline_simulation_vislist_{}.ms'.format(dir_vis, v),
            [corrupted_vislist[v]]
        )
        for v, _ in enumerate(corrupted_vislist)
    ]

    print('About to run predict and corrupt to get corrupted visibility, and write files')
    rsexecute.compute(export_list, sync=True)


def ical(parameters):
    """Iterative self-calibration.

    Calibrate visibilities and produce continuum image.

    :param parameters: pipeline parameters (dict)

    """
    # Get parameters, setting default value if not present
    nfreqwin = parameters.get('nfreqwin', 8)
    dir_vis = '/buffer/' + parameters.get('buffer_vis')
    dir_img = '/buffer/' + parameters.get('buffer_img')

    cellsize = 0.0005
    npixel = 1024
    pol_frame = PolarisationFrame("stokesI")
    centre = nfreqwin // 2

    rsexecute.run(init_logging)

    # Load data from simulation
    vis_list = [
        rsexecute.execute(create_blockvisibility_from_ms)(
            '{}/ska_pipeline_simulation_vislist_{}.ms'.format(dir_vis, v)
        )[0]
        for v in range(nfreqwin)
    ]

    print('Reading visibilities')
    vis_list = rsexecute.persist(vis_list)

    model_list = [
        rsexecute.execute(create_image_from_visibility)(
            v, npixel=npixel, cellsize=cellsize, polarisation_frame=pol_frame
        )
        for v in vis_list
    ]

    print('Creating model images')
    model_list = rsexecute.persist(model_list)

    imaging_context = 'ng'
    vis_slices = 1

    controls = create_calibration_controls()

    controls['T']['first_selfcal'] = 1
    controls['T']['phase_only'] = True
    controls['T']['timeslice'] = 'auto'

    controls['G']['first_selfcal'] = 3
    controls['G']['timeslice'] = 'auto'

    controls['B']['first_selfcal'] = 4
    controls['B']['timeslice'] = 1e5

    ical_list = ical_list_rsexecute_workflow(
        vis_list,
        model_imagelist=model_list,
        context=imaging_context,
        vis_slice=vis_slices,
        scales=[0, 3, 10], algorithm='mmclean',
        nmoment=2, niter=1000,
        fractional_threshold=0.1,
        threshold=0.1, nmajor=5, gain=0.25,
        deconvolve_facets=1,
        deconvolve_overlap=0,
        restore_facets=8,
        timeslice='auto',
        psf_support=128,
        global_solution=False,
        calibration_context='T',
        do_selfcal=True
    )

    print('About to run ICAL workflow')
    result = rsexecute.compute(ical_list, sync=True)

    print('Writing images')
    deconvolved = result[0][centre]
    residual = result[1][centre][0]
    restored = result[2][centre]
    export_form = '{}/ska_pipeline_ical_{}.fits'
    export_list = [
        rsexecute.execute(export_image_to_fits)(
            deconvolved, export_form.format(dir_img, 'deconvolved')
        ),
        rsexecute.execute(export_image_to_fits)(
            residual, export_form.format(dir_img, 'residual')
        ),
        rsexecute.execute(export_image_to_fits)(
            restored, export_form.format(dir_img, 'restored')
        )
    ]
    rsexecute.compute(export_list, sync=True)
