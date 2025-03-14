from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import _init_paths

import os
import sys
import cv2
import json
import copy
import numpy as np
from lib.opts import opts
from lib.detector import Detector

image_ext = ['jpg', 'jpeg', 'png', 'webp']
video_ext = ['mp4', 'mov', 'avi', 'mkv']
time_stats = ['tot', 'load', 'pre', 'net', 'dec', 'post', 'merge', 'display']

def demo(opt):
  os.environ['CUDA_VISIBLE_DEVICES'] = opt.gpus_str
  opt.debug = max(opt.debug, 1)
  detector = Detector(opt)

  if opt.demo == 'webcam' or \
    opt.demo[opt.demo.rfind('.') + 1:].lower() in video_ext:
    is_video = True
    # demo on video stream
    cam = cv2.VideoCapture(0 if opt.demo == 'webcam' else opt.demo)
  else:
    is_video = False
    # Demo on images sequences
    if os.path.isdir(opt.demo):
      image_names = []
      ls = os.listdir(opt.demo)
      for file_name in sorted(ls):
          ext = file_name[file_name.rfind('.') + 1:].lower()
          if ext in image_ext:
              image_names.append(os.path.join(opt.demo, file_name))
    else:
      # Demo on single image
      image_names = [opt.demo]
      
  # config output video setting
  out = None
  out_name = opt.demo[opt.demo.rfind('/')+1:]
  if is_video:
    out_name = out_name[:out_name.rfind('.')]
  print(out_name)
  if opt.save_video:
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')
    # fourcc = cv2.VideoWriter_fourcc(*'H264')
    # fourcc = cv2.VideoWriter_fourcc(*'I420')
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    save_format = '.avi'

  if opt.debug < 5:
    detector.pause = False
  
  results = {}
  save_path =  '../results/{}/{}'.format(out_name, opt.exp_id + '_' + out_name)
  if not os.path.exists(save_path[:save_path.rfind('/')]):
    os.makedirs(save_path[:save_path.rfind('/')])
  if not os.path.exists(save_path) and opt.save_image:
    # saved image dir
    os.makedirs(save_path)
  
  cnt = 0  
  while True:
      if is_video:
        _, img = cam.read()
      else:
        if cnt >= len(image_names):
          img = None
        else:
          img = cv2.imread(image_names[cnt])
      cnt += 1
      
      # finish all
      if img is None:
        save_and_exit(opt, out, results, out_name, save_path)
        
      # Initialize output video
      if opt.save_video and cnt==1:
        in_video_h, in_video_w = img.shape[0:2]
        out = cv2.VideoWriter(save_path+'_video'+save_format,fourcc, opt.save_framerate, (
            in_video_w, in_video_h))

      # resize the original video for saving video results
      if opt.resize_video:
        img = cv2.resize(img, (opt.video_w, opt.video_h))

      # skip the first X frames of the video
      if cnt < opt.skip_first:
        continue
      
      cv2.imshow('input', img)
      # track or detect the image.
      ret = detector.run(img)

      # log run time
      time_str = 'frame {} |'.format(cnt)
      for stat in time_stats:
        time_str = time_str + '{} {:.3f}s |'.format(stat, ret[stat])
      print(time_str)

      # results[cnt] is a list of dicts:
      #  [{'bbox': [x1, y1, x2, y2], 'tracking_id': id, 'category_id': c, ...}]
      results[cnt] = ret['results']

      # save debug image to video
      if opt.save_results:
        if opt.save_video:
          out.write(ret['generic'])
        if opt.save_image:
          cv2.imwrite(save_path+'/demo{}.jpg'.format(cnt), ret['generic'])

              
      # esc to quit and finish saving video
      if cv2.waitKey(1) == 27:
        save_and_exit(opt, out, results, out_name, save_path)

def save_and_exit(opt, out=None, results=None, out_name='', save_path='../results/res/res'):
  if not os.path.exists(save_path[:save_path.rfind('/')]):
    os.makedirs(save_path[:save_path.rfind('/')])
  if opt.save_results and (results is not None):
    json.dump(_to_list(copy.deepcopy(results)), 
              open(save_path+'_ResData.json', 'w'))
  if opt.save_video and out is not None:
    out.release()
  print('saving result to', save_path)
  print('out_name:',out_name)
  sys.exit(0)

def _to_list(results):
  for img_id in results:
    for t in range(len(results[img_id])):
      for k in results[img_id][t]:
        if isinstance(results[img_id][t][k], (np.ndarray, np.float32)):
          results[img_id][t][k] = results[img_id][t][k].tolist()
  return results

if __name__ == '__main__':
  opt = opts().init()
  demo(opt)
