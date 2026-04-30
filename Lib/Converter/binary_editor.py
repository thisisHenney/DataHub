import struct
from pathlib import Path

import numpy as np


class E8BinaryEditor:
    def __init__(self):
        self.data = np.array([])
        self.header = ['pos_x', 'pos_y', 'vel_x', 'vel_y', 'target_speed', 'goal_x', 'goal_y']

    def read_binary_file(self, file_path):
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.is_file():
            raise FileNotFoundError

        with open(file_path, 'rb') as f:
            row_count = np.fromfile(f, dtype='<u4', count=1)[0]
            data = np.fromfile(f, dtype='<f4', count=row_count * 7)
            self.data = data.reshape(row_count, 7)

    def write_binary_file(self, file_path):
        if isinstance(file_path, str):
            file_path = Path(file_path)

        with open(file_path, 'wb') as f:
            N = self.data.shape[0]
            f.write(struct.pack('<I', N))  # (1) uint32로 행 수 쓰기
            flat = self.data.astype(np.float32).ravel()  # (2) float32 7×N개를 한꺼번에 패킹 후 쓰기
            f.write(struct.pack(f'<{flat.size}f', *flat))

    def write_ascii_csv_file(self, file_path):
        if isinstance(file_path, str):
            file_path = Path(file_path)

        np.savetxt(str(file_path.absolute()), self.data,
                   delimiter=',', header=','.join(self.header), comments='#',  fmt='%0.6f')


if __name__ == '__main__':
    b_file_path = Path('./binary_data_test')
    editor = E8BinaryEditor()
    editor.read_binary_file(b_file_path)
    print(editor.data)
