#!/usr/bin/env python3


import sys, os, shutil



def create_folder():
    try:
        os.makedirs(dest_folder)
    except Exception as e:
        print(f"[ERROR]: Failed to create destination folder '{dest_folder}': {e}")
        return

if __name__ == '__main__':
    done_folder = '__done'
    folder_path = os.path.abspath(sys.argv[1])
    dest_folder = f'{folder_path}/{done_folder}'
    dataset = set(sys.argv[2].split('::'))

    ll = []
    for file_name in os.listdir(folder_path):
        if file_name.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
            print(file_name)
            if file_name in dataset:
                ll.append(file_name)

    print(dataset)
    print(ll)
    if ll:
        print(ll)
        if not os.path.exists(dest_folder):
            create_folder()

        for name in ll:
            try:
                shutil.move(f'{folder_path}/{name}', f'{dest_folder}/{name}')
                print(f'[MOVED]: {name}')
            except Exception as e:
                pass

    print('[COMPLETE]')
