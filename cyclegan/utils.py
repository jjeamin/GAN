import tensorflow as tf
from tensorflow.contrib import slim
from scipy import misc
import os, random
import numpy as np
from tqdm import tqdm
import request
import math
import zipfile

# https://people.eecs.berkeley.edu/~taesung_park/CycleGAN/datasets/
# https://people.eecs.berkeley.edu/~tinghuiz/projects/pix2pix/datasets/

class reader:
    def __init__(self, dir_name, batch_size,resize):
        self.dir_name = dir_name
        self.batch_size = batch_size
        self.resize = resize
        # file list
        self.file_list = os.listdir(self.dir_name)
        # total batch num
        self.leng = len(self.file_list)
        self.total_batch = self.leng // self.batch_size
        # index
        self.index = 0
        # shuffle
        np.random.shuffle(self.file_list)

    def getList(self):
        return self.file_list

    def getTotalNum(self):
        return len(self.file_list)

    def next_batch(self):
        if self.index == self.total_batch:
            np.random.shuffle(self.file_list)
            self.index = 0

        # image random choice
        batch = []

        file_list_batch = self.file_list[self.index * self.batch_size:(self.index + 1) * self.batch_size]
        self.index += 1

        # 6331번
        for file_name in file_list_batch:
            dir_n = self.dir_name + file_name
            img = misc.imread(dir_n)
            res = misc.imresize(img, self.resize)
            batch.append(res)

        return np.array(batch).astype(np.float32)

class dataset:
    def __init__(self,url,filename):
        self.url = url
        self.filename = filename
        self.current = '//'.join(os.getcwd().split('\\'))+'//'+filename

    def download(self):
        if os.path.exists(self.current):
            print('already existing file')
            return

        wrote = 0
        chunkSize = 1024
        r = request.get(self.url, stream=True)
        total_size = int(r.headers['Content-Length'])
        with open(self.filename, 'wb') as f:
            for data in tqdm(r.iter_content(chunkSize), total=math.ceil(total_size // chunkSize), unit='KB',
                             unit_scale=True):
                wrote = wrote + len(data)
                f.write(data)
        print('download success')
        return

    def upzip(self,savepath='.'):
        if os.path.isdir(self.current[:-4]):
            print('already existing folder')
            return

        with zipfile.ZipFile(self.filename,'r') as zf:
            zf.extractall(path=savepath)
            zf.close()
        print('unzip success')

def load_test_data(image_path, size=256):
    img = misc.imread(image_path, mode='RGB')
    img = misc.imresize(img, [size, size])
    img = np.expand_dims(img, axis=0)
    img = preprocessing(img)

    return img

def preprocessing(x):
    x = x/127.5 - 1 # -1 ~ 1
    return x

def augmentation(image, augment_size):
    seed = random.randint(0, 2 ** 31 - 1)
    ori_image_shape = tf.shape(image)
    image = tf.image.random_flip_left_right(image, seed=seed)
    image = tf.image.resize_images(image, [augment_size, augment_size])
    image = tf.random_crop(image, ori_image_shape, seed=seed)
    return image

def save_images(images, size, image_path):
    return imsave(inverse_transform(images), size, image_path)

def inverse_transform(images):
    return (images+1.) / 2

def imsave(images, size, path):
    return misc.imsave(path, merge(images, size))

def merge(images, size):
    h, w = images.shape[1], images.shape[2]
    img = np.zeros((h * size[0], w * size[1], 3))
    for idx, image in enumerate(images):
        i = idx % size[1]
        j = idx // size[1]
        img[h*j:h*(j+1), w*i:w*(i+1), :] = image

    return img

def show_all_variables():
    model_vars = tf.trainable_variables()
    slim.model_analyzer.analyze_vars(model_vars, print_info=True)

def check_folder(log_dir):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

def batch_save(X,nh_nw,path):
    nh, nw = nh_nw
    h, w = X.shape[1], X.shape[2]
    img = np.zeros((h * nh, w * nw, 3))

    for n, x in enumerate(X):
        j = int(n / nw)
        i = int(n % nw)
        img[j * h:j * h + h, i * w:i * w + w, :] = x

    misc.imsave(path,img)