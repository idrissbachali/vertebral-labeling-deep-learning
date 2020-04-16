import sys
import os
import argparse
sys.path.insert(0, '/home/lucas/sct')
from spinalcordtoolbox.cropping import ImageCropper, BoundingBox
from spinalcordtoolbox.image import Image
from spinalcordtoolbox.utils import Metavar, SmartFormatter
import scripts.sct_utils as sct

import torch
from models import *
from test import *
from Data2array import *
import numpy as np
sys.path.insert(0, '../../../sct/sct')
import nibabel as nib


def get_parser():
    # Mandatory arguments
    parser = argparse.ArgumentParser(
        description="tools to detect C2/C3 intervertebral disc with countception deep learning network ",
        epilog="EXAMPLES:\n",
        add_help=None,
        formatter_class=SmartFormatter,
        prog=os.path.basename(__file__).strip('.py'))

    mandatoryArguments = parser.add_argument_group("\nMANDATORY ARGUMENTS")
    mandatoryArguments.add_argument(
        '-i',
        required=True,
        help="Input image. Example: t2.nii.gz",
        metavar=Metavar.file,
    )
    mandatoryArguments.add_argument(
        '-c',
        required=True,
        help="contrast",
    )
    optional = parser.add_argument_group("\nOPTIONAL ARGUMENTS")
    optional.add_argument(
        '-h',
        '--help',
        action='help',
        help="Show this help message and exit")
    optional.add_argument(
        '-o',
        help="output name",
        metavar=Metavar.str,
    )
    optional.add_argument(
        '-image',
        help="if 1 Return an image as output,else return coord",
        metavar=Metavar.int,
        default=0,
    )
    optional.add_argument(
        '-net',
        help="Network to use",
        default='CC',
    )

    return parser


def main(args=None):
    """
    Main function
    :param args:
    :return:
    """
    # get parser args
    if args is None:
        args = None if sys.argv[1:] else ['--help']
    parser = get_parser()
    arguments = parser.parse_args(args=args)
    Im_input = Image(arguments.i)
    contrast = arguments.c

    global cuda_available
    cuda_available = torch.cuda.is_available()

    model = ModelCountception_v2(inplanes=1, outplanes=1)
    if cuda_available:
        model = model.cuda()
    model = model.float()

    if contrast == 't1':
        model.load_state_dict(torch.load('~/luroub_local/lurou_local/deep_VL_2019/ivado_med/scripts_vertebral_labeling/checkpoints/Countception_c2T1.model', map_location='cpu')['model_weights'])

    elif contrast == 't2':
        model.load_state_dict(torch.load('/home/GRAMES.POLYMTL.CA/luroub/luroub_local/lurou_local/deep_VL_2019/ivado_med/scripts_vertebral_labeling/checkpoints/Countception_floatC2T2.model',map_location='cpu')['model_weights'])

    else:
        sct.printv('Error...unknown contrast. please select between t2 and t1.')
        return 100
    sct.printv('retrieving input...')
    Im_input.change_orientation('RPI')
    arr = np.array(Im_input.data)
    #debugging

    sct.printv(arr.shape)
    ind = int(np.round(arr.shape[0] / 2))
    inp = np.mean(arr[ind - 2:ind + 2, :, :], 0)
    pad = int(np.ceil(arr.shape[2] / 32))*32
    img_tmp = np.zeros((160, pad), dtype=np.float64)
    img_tmp[0:inp.shape[0], 0:inp.shape[1]] = inp
    sct.printv(inp.shape)
    inp = np.expand_dims(img_tmp,-1)
    sct.printv('Predicting coordinate')
    
    coord = prediction_coordinates(inp, model, [0, 0], 0, test=False, aim='c2')
    mask_out = np.zeros(arr.shape)
    if len(coord) < 1 or coord == [0, 0]:
        sct.printv('C2/C3 detection failed. Please provide manual initialisation')
    print(arguments.image)
   # if int(arguments.image) == 1:
    for x in coord:
        mask_out[ind, x[1], x[0]] = 10
    sct.printv('saving image')
    imsh = arr.shape
    to_save = Image(param=[imsh[0], imsh[1], imsh[2]], hdr=Im_input.header)
    to_save.data = mask_out
    if arguments.o is not None:
        to_save.save(arguments.o)
    else:
        to_save.save('labels_c2.nii')
    #else:
     #   return coord


if __name__ == "__main__":
    main()
