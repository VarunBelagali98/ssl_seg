import torch
import torchvision
import torch.optim as optim
#from dataloader import load_data
from dataloaders.Super_dataloader import load_data
from torch.utils import data as data_utils
from tqdm import tqdm
from torchsummary import summary
import argparse
import numpy as np 
import cv2
import os
from models.unet import UNet as M
import matplotlib.pyplot as plt 

use_cuda = torch.cuda.is_available()

parser = argparse.ArgumentParser(description='Code to test model')

parser.add_argument("--fold", help="fold index [1-5]", required=True, type=int)

parser.add_argument("--batch_size", help="batch size", default=1, type=int)

parser.add_argument('--root_data', help='data folder path', default="../training/training/training/", type=str)

parser.add_argument('--fold_data', help='fold files path', default="../Data_files/", type=str)

parser.add_argument("--weight_root", help="weight folder", default="/content//gdrive/MyDrive/colab-data/weights/", type=str)

parser.add_argument("--eval_root", help="results folder", default="/content//gdrive/MyDrive/colab-data/Dice/", type=str)

parser.add_argument("--model_name", help="name of the weight file", required=True, type=str)

args = parser.parse_args()

args = parser.parse_args()

def save_samples(test_data_loader, device, model):
	prog_bar = tqdm(enumerate(test_data_loader))
	count = 0
	if not os.path.exists('./samples/'):
		os.mkdir('./samples')

	model.eval()

	for step, data in prog_bar:
		# Move data to CUDA device
		x1, x2 = data[0], data[1]
		x1 = x1.to(device)
		x2 = x2.to(device)

		preds, _ = model.forward(x1)

		x1 = x1.cpu().detach().numpy()
		
		for pred_i in range(1):
			pred = preds
			pred = pred.cpu().detach().numpy()
			pred = pred > 0.5 #(1.0 / (pred.shape[-1] * pred.shape[-2]))
			#pred = np.argmax(pred, axis=1)
			pred = pred.astype(int)

			for i in range(x1.shape[0]):
				img = x1[i, 0, :, :] * 255
				img = img.astype(int)
				seg = pred[i, 0, :, :] * 255
				cv2.imwrite('./samples/'+str(count)+".png", img)
				cv2.imwrite('./samples/'+str(count)+"_seg"+str(pred_i) +".png", seg)
				#plt.imsave('./samples/'+str(count)+"_seg.png", seg)
				if pred_i == 0:
					count = count + 1
		
			if count > 100:
				return

def test(test_data_loader, device, model):
	prog_bar = tqdm(enumerate(test_data_loader))
	dice_list = []

	model.eval()

	for step, data in prog_bar:

		# Move data to CUDA device
		inputs, gt = data[0], data[1]
		inputs = inputs.to(device)
		gt = gt.to(device)

		dices = model.cal_score(inputs, gt)
		dice_list.extend(dices)
		prog_bar.set_description('Test Dice loss: {:.4f}'.format(sum(dice_list)/len(dice_list)))

	return dice_list

if __name__ == "__main__":
	fold = args.fold
	model_name = args.model_name
	batch_size = args.batch_size
	TRAINING_PATH = args.root_data
	FOLD_PATH = args.fold_data + 'fold_files/annfiles_fold' #"fold_struct/fold"
	ROOT_WEIGHTPATH = args.weight_root
	Vid_to_IMG_PATH = args.fold_data + "videoId_to_imgIdx/"
	EVAL_PATH = args.eval_root
	
	WEIGTH_PATH = ROOT_WEIGHTPATH + model_name + ".pth"

	# Dataset and Dataloader setup
	#test_dataset = load_data(fold, 2, TRAINING_PATH=TRAINING_PATH, FOLD_PATH=FOLD_PATH, Vid_to_IMG_PATH=Vid_to_IMG_PATH)
	test_dataset = load_data(fold, 2, TRAINING_PATH=TRAINING_PATH, FOLD_PATH=FOLD_PATH)
	test_dataset.datalist = list(range(55750, 55750+3500))

	test_data_loader = data_utils.DataLoader(
		test_dataset, batch_size=batch_size)

	device = torch.device("cuda" if use_cuda else "cpu")

	# Model
	model = M().to(device)
	#summary(model, (1, 224, 224))

	# Load weights
	print(WEIGTH_PATH)
	model.load_state_dict(torch.load(WEIGTH_PATH))

	# Test!
	with torch.no_grad():
		res = test(test_data_loader, device, model)
	#with open(EVAL_PATH+ model_name +'_test_dice.txt', 'w') as f_test:
	#	for item in res:
	#		f_test.write("%s\n" % item)

	# Save samples
	with torch.no_grad():
		save_samples(test_data_loader, device, model)