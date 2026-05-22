from enum import Enum
from pathlib import Path
from typing import Union

import numpy as np
import vtk
from pyproj import Transformer

from vtkmodules.util import numpy_support
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPolyData, vtkDataSetAttributes
from vtkmodules.vtkCommonCore import vtkPoints, VTK_FLOAT, VTK_UNSIGNED_CHAR
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersCore import vtkAppendPolyData, vtkGlyph3D
from vtkmodules.vtkFiltersGeneral import vtkVertexGlyphFilter, vtkTransformFilter
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter, vtkImageDataGeometryFilter, vtkGeometryFilter
from vtkmodules.vtkFiltersSources import vtkArrowSource
from vtkmodules.vtkIOLegacy import vtkDataSetWriter
from vtkmodules.vtkRenderingCore import vtkImageActor, vtkPolyDataMapper, vtkActor, vtkCompositePolyDataMapper, \
    vtkDataSetMapper

import json
from Lib.Json.JsonRW import JsonRW


class CompanyType(Enum):
    Pintel = 1
    Vueron = 2
    KETI = 3


class VtkJsonConverter:
    def __init__(self):
        self.array = np.array([])
        self.company: CompanyType = None
        self.vtk_data = None
        self.g2k_trs = Transformer.from_crs("EPSG:4326", "EPSG:5179", always_xy=False)
        self.k2g_trs = Transformer.from_crs("EPSG:5179", "EPSG:4326", always_xy=False)

        self.rainbow_lut = self._make_rainbow_lut()
        pass

    def set_data_company(self, company: CompanyType):
        self.company = company

    def load_array_from_json_string(self, string: str, encoding='UTF-8'):
        reader = JsonRW()
        reader.load(string)
        return self._load_array_from_json(reader)

    def load_array_from_reader(self, reader: JsonRW):
        return self._load_array_from_json(reader)

    def load_array_from_json_file(self, file_path: Path, encoding='UTF-8'):
        reader = JsonRW()
        reader.read(file_path, encoding=encoding)
        self._load_array_from_json(reader)

    def make_vtk(self):
        if self.company is None:
            raise TypeError("CompannyType is missing. Import CompanyType and Do 'set_data_company()'")

        if self.company == CompanyType.Pintel:
            self._make_vtk_from_pintel()
        elif self.company == CompanyType.Vueron:
            self._make_vtk_from_vueron()
        elif self.company == CompanyType.KETI:
            self._make_vtk_from_keti()

        return self.vtk_data

    def get_vtk_data(self):
        if self.vtk_data is None:
            raise TypeError("There is no vtkData. Do 'make_vtk()' first")

        return self.vtk_data

    def get_vtk_actor(self):
        if self.vtk_data is None:
            raise TypeError("There is no vtkData. Do 'make_vtk()' first")

        if self.company == CompanyType.Pintel:
            surfaceFilter = vtk.vtkDataSetSurfaceFilter()
            surfaceFilter.SetInputData(self.vtk_data)

            removeGhosts = vtk.vtkRemoveGhosts()
            removeGhosts.SetInputConnection(surfaceFilter.GetOutputPort())

            mapper = vtkDataSetMapper()
            mapper.SetInputConnection(removeGhosts.GetOutputPort())
            # mapper.SetInputData(self.vtk_data)
            mapper.SetScalarVisibility(True)

            mapper.SetScalarModeToUseCellFieldData()
            mapper.SelectColorArray('number of people')
            mapper.SetColorModeToMapScalars()
            mapper.SetScalarRange(0, 25)
            mapper.SetLookupTable(self.rainbow_lut)

            actor = vtkActor()
            actor.SetMapper(mapper)

        elif self.company == CompanyType.Vueron:
            arrow_source = vtkArrowSource()
            arrow_source.SetTipLength(0.5)
            arrow_source.SetTipRadius(0.2)
            arrow_source.SetShaftRadius(0.05)

            glyph = vtkGlyph3D()
            glyph.SetSourceConnection(arrow_source.GetOutputPort())
            glyph.SetInputData(self.vtk_data)
            glyph.SetVectorModeToUseVector()
            # glyph.SetScaleModeToScaleByVector()
            glyph.SetScaleModeToDataScalingOff()
            glyph.SetColorModeToColorByVector()
            glyph.SetScaleFactor(2)
            glyph.OrientOn()
            glyph.Update()

            geometry_filter = vtkGeometryFilter()
            geometry_filter.SetInputConnection(glyph.GetOutputPort())

            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(glyph.GetOutputPort())
            mapper.ScalarVisibilityOn()
            # mapper.SetScalarModeToUseCellData()
            mapper.SetScalarModeToUsePointFieldData()
            mapper.SelectColorArray('velocity')
            mapper.SetColorModeToMapScalars()
            # mapper.SelectColorArray()
            mapper.SetColorModeToDefault()
            mapper.SetScalarRange(0, 5)
            mapper.SetLookupTable(self.rainbow_lut)

            actor = vtkActor()
            actor.SetMapper(mapper)
            # actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # 눈에 띄는 빨간색
            actor.GetProperty().SetLineWidth(2)
            actor.GetProperty().SetPointSize(5)

        elif self.company == CompanyType.KETI:
            mapper = vtkCompositePolyDataMapper()
            mapper.SetInputData(self.vtk_data)
            mapper.ScalarVisibilityOff()

            actor = vtkActor()
            actor.SetMapper(mapper)

        else:
            actor = vtkActor()
            raise TypeError

        return actor

    def write_json_string(self):
        if self.company != CompanyType.KETI:
            raise TypeError("This function is supported only in CompanyType.KETI")
        if self.vtk_data is None:
            raise TypeError("There is no vtkData. Do 'make_vtk()' first")

        pass

    def write_json_file(self):
        if self.company != CompanyType.KETI:
            raise TypeError("This function is supported only in CompanyType.KETI")
        if self.vtk_data is None:
            raise TypeError("There is no vtkData. Do 'make_vtk()' first")

        pass

    def write_vtk_file(self, file_path: Union[str, Path]):
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if self.vtk_data is None:
            raise TypeError("There is no vtkData. Do 'make_vtk()' first")

        writer = vtkDataSetWriter()
        writer.SetFileName(str(file_path.absolute()))
        writer.SetInputData(self.vtk_data)
        # writer.SetFileTypeToASCII()
        writer.SetFileTypeToBinary()
        writer.Write()

    def gps_to_korean(self, lat, long):
        # lat: 위도  long: 경도
        y, x = self.g2k_trs.transform(lat, long)
        return x, y

    def korean_to_gps(self, ew, ns):
        # ew: 동서방향 좌표   ns: 남북방향 좌표
        return self.k2g_trs.transform(ns, ew)

    def merge_vtk_data_in_grid(self, base_grid: vtk.vtkImageData,
                               pintel_data: list[vtk.vtkImageData]=[],
                               vueron_data: list[vtk.vtkPolyData]=[],
                               keti_data: vtk.vtkPolyData=None,
                               write_file_path: Path=None):

        base_origin = np.array(base_grid.GetOrigin())[:2]  # world 좌표
        dx, dy = base_spacing = np.array(base_grid.GetSpacing())[:2]  # dx,dy
        base_dims_points = np.array(base_grid.GetDimensions())[:2] # 포인트 수
        nx, ny = base_cell_dims = base_dims_points - 1  # 셀 수

        all_density_arrays = []
        all_velocity_arrays = []

        # ==============================

        sum_num_data = np.zeros(base_cell_dims[::-1], dtype=np.float64)
        count_num_data = np.zeros(base_cell_dims[::-1], dtype=np.int32)
        sum_vel_data = np.zeros((ny, nx, 3), dtype=np.float64)
        count_vel_data = np.zeros((ny, nx, 3), dtype=np.int32)

        for grid in pintel_data:
            sub_origin = np.array(grid.GetOrigin())[:2]
            sub_spacing = np.array(grid.GetSpacing())[:2]
            assert np.allclose(sub_spacing, base_spacing), "dx, dy error"
            sub_dims_points = np.array(grid.GetDimensions())[:2]
            snx, sny = sub_cell_dims = sub_dims_points - 1  # (nx, ny) in cells

            offset_cells = np.round((sub_origin - base_origin) / base_spacing).astype(int)
            i0, j0 = offset_cells
            i1, j1 = offset_cells + sub_cell_dims  # exclusive

            vtk_arr = grid.GetCellData().GetArray("number of people")
            np_arr = numpy_support.vtk_to_numpy(vtk_arr).reshape(-1, 1)
            np_arr3 = np_arr.reshape(tuple(sub_cell_dims[::-1]), order='C')

            if np_arr3.shape[0] == 0 or np_arr3.shape[1] == 0:
                continue

            if j0 < 0:
                continue
            if j1 > sum_num_data.shape[0]:
                continue
            if i0 < 0:
                continue
            if i1 > sum_num_data.shape[1]:
                continue

            # print(np_arr3.shape)
            # print(sum_num_data.shape, j0+1, j1+1, i0, i1)
            # print(sum_num_data[j0+1:j1+1, i0:i1].shape)
            #
            # if j0 < 0:
            #     np_arr3 = np_arr3[j0:, :]
            #     print(f"cutted left {j0}")
            # if j1 > sum_num_data.shape[0]:
            #     np_arr3 = np_arr3[:sum_num_data.shape[0]-j1-1, :]
            #     print(f"cutted right {sum_num_data.shape[0]-j1-1}")
            # if i0 < 0:
            #     np_arr3 = np_arr3[:, i0:]
            #     print(f"cutted bottom {i0}")
            # if i1 > sum_num_data.shape[1]:
            #     np_arr3 = np_arr3[:, :sum_num_data.shape[1]-i1]
            #     print(f"cutted right {sum_num_data.shape[1]-i1}")
            # print(np_arr3.shape)

            sum_num_data[j0+1:j1+1, i0:i1] = sum_num_data[j0+1:j1+1, i0:i1] + np_arr3
            count_num_data[j0+1:j1+1, i0:i1] += 1

            vtk_arr = grid.GetCellData().GetArray("velocity")
            np_arr3 = numpy_support.vtk_to_numpy(vtk_arr).reshape(sny, snx, 3)

            sum_vel_data[j0 + 1:j1 + 1, i0:i1, :] += np_arr3
            count_vel_data[j0 + 1:j1 + 1, i0:i1, :] += 1

        avg_data = np.zeros_like(sum_num_data, order='C')
        mask = count_num_data > 0
        avg_data[mask] = sum_num_data[mask] / count_num_data[mask]
        flat_avg = avg_data.flatten(order='C') / (base_spacing[0] * base_spacing[1])
        all_density_arrays.append(flat_avg)
        self._append_cell_data_to_image(base_grid, 'pintel_density', flat_avg, nx, ny)

        avg_data = np.zeros_like(sum_vel_data, order='C')
        mask = count_vel_data > 0
        avg_data[mask] = sum_vel_data[mask] / count_vel_data[mask]
        flat_avg = avg_data.reshape((-1, 3), order='C')
        all_velocity_arrays.append(flat_avg)
        self._append_cell_data_to_image(base_grid, 'pintel_velocity', flat_avg, nx, ny)

        # =============================================

        vueron_num_array_list = []
        vueron_v_array_list = []
        for point_cloud in vueron_data:
            x_edges = base_origin[0] + np.arange(nx + 1) * dx
            y_edges = base_origin[1] + np.arange(ny + 1) * dy

            pts_np = vtk_to_numpy(point_cloud.GetPoints().GetData())
            x_pc = pts_np[:, 0]
            y_pc = pts_np[:, 1]

            hist, _, _ = np.histogram2d(x_pc, y_pc, bins=[x_edges, y_edges])
            vueron_num_array_list.append(hist.T)

            vel_arr = point_cloud.GetPointData().GetArray("velocity")
            vel_np = vtk_to_numpy(vel_arr)

            ix = np.clip(np.digitize(x_pc, x_edges) - 1, 0, nx - 1)
            iy = np.clip(np.digitize(y_pc, y_edges) - 1, 0, ny - 1)
            cell_idx = iy * nx + ix  # flat index, 0 ≤ idx < nx*ny
            num_cells = nx * ny

            counts_flat = np.bincount(cell_idx, minlength=num_cells)

            sum_vel = np.zeros((num_cells, 3), dtype=vel_np.dtype)
            np.add.at(sum_vel, cell_idx, vel_np)

            avg_vel = np.zeros_like(sum_vel)
            np.divide(sum_vel, counts_flat[:, None], out=avg_vel, where=counts_flat[:, None] > 0)
            vueron_v_array_list.append(avg_vel)

        if vueron_num_array_list:
            vueron_num_array = self._do_average_array(vueron_num_array_list)
            vueron_d_array = vueron_num_array.ravel(order='C') / (base_spacing[0] * base_spacing[1])
            all_density_arrays.append(vueron_d_array)
            self._append_cell_data_to_image(base_grid, 'vueron_density', vueron_d_array, nx, ny)

            vueron_v_array = self._do_average_array(vueron_v_array_list)
            all_velocity_arrays.append(vueron_v_array)
            self._append_cell_data_to_image(base_grid, 'vueron_velocity', vueron_v_array, nx, ny)

        # ==============================================

        if keti_data is not None:
            n_i, n_j = base_cell_dims
            flat_size = n_i * n_j
            flat_sum = np.zeros(flat_size, dtype=np.float64)
            flat_count = np.zeros(flat_size, dtype=np.int32)
            flat_sum2 = np.zeros((flat_size, 3), dtype=np.float64)
            flat_count2 = np.zeros(flat_size, dtype=np.int32)

            cell_arr1 = keti_data.GetCellData().GetArray('density')
            vals1 = numpy_support.vtk_to_numpy(cell_arr1)  # shape (N,)
            cell_arr2 = keti_data.GetCellData().GetArray('direction')
            vals2 = numpy_support.vtk_to_numpy(cell_arr2)  # shape (N, 3)

            centers_f = vtk.vtkCellCenters()
            centers_f.SetInputData(keti_data)
            centers_f.Update()
            pts_vtk = centers_f.GetOutput().GetPoints().GetData()
            pts = numpy_support.vtk_to_numpy(pts_vtk)[:, :2]

            idxs = np.floor((pts - base_origin) / base_spacing).astype(int)
            idxs = np.minimum(np.maximum(idxs, [0, 0]), base_cell_dims - 1)

            flat_idx = idxs[:, 1] * n_i + idxs[:, 0]

            np.add.at(flat_sum, flat_idx, vals1)
            np.add.at(flat_count, flat_idx, 1)

            np.add.at(flat_sum2, flat_idx, vals2)
            np.add.at(flat_count2, flat_idx, 1)

            flat_avg = np.zeros_like(flat_sum)
            mask = flat_count > 0
            flat_avg[mask] = flat_sum[mask] / flat_count[mask]
            all_density_arrays.append(flat_avg)
            self._append_cell_data_to_image(base_grid, 'keti_density', flat_avg, nx, ny)

            flat_avg2 = np.zeros_like(flat_sum2)
            mask = flat_count2 > 0
            flat_avg2[mask] = flat_sum2[mask] / np.repeat(flat_count2[mask][:, np.newaxis], 3, axis=1)
            all_velocity_arrays.append(flat_avg2)
            self._append_cell_data_to_image(base_grid, 'keti_velocity', flat_avg2, nx, ny)

        all_density_array = self._do_average_array(all_density_arrays)
        self._append_cell_data_to_image(base_grid, 'density', all_density_array, nx, ny)

        all_velocity_array = self._do_average_array(all_velocity_arrays)
        self._append_cell_data_to_image(base_grid, 'velocity', all_velocity_array, nx, ny)

        self.vtk_data = base_grid

        return self.vtk_data

    def make_json_dict_for_keti(self, timestamp, index: tuple[slice or int, slice or int]=None):
        if not isinstance(self.vtk_data, vtkImageData):
            raise TypeError(f"KETI data must be grid data(vtkImageData). Current data is: {self.vtk_data.__name__}")

        # (row, col) = index
        # eg) [:, 1] = (slice(None), 1)  //  [:3, 2:-2] = (slice(None, 3), slice(2, -2))
        # eg) [2:, :] = (slice(2, None), slice(None))

        dx, dy = base_spacing = np.array(self.vtk_data.GetSpacing())[:2]  # dx,dy
        base_dims_points = np.array(self.vtk_data.GetDimensions())[:2]  # 포인트 수
        nx, ny = base_dims_points - 1  # 셀 수

        density_array_flat = numpy_support.vtk_to_numpy(self.vtk_data.GetCellData().GetArray('density'))
        density_array = density_array_flat.reshape((ny, nx), order="C")
        velocity_array_flat = numpy_support.vtk_to_numpy(self.vtk_data.GetCellData().GetArray('velocity'))
        velocity_array = velocity_array_flat.reshape((ny, nx, 3), order="C")[:, :, :2]
        if index is not None:
            (row, col) = index
            density_array = density_array[row, col]
            nx, ny = density_array.shape
            velocity_array = velocity_array[row, col, :1]

        dictionary = {
            "timestamp": timestamp,
            "width": int(nx),
            "height": int(ny),
            "gridsize": float(dx),
            "density": density_array.tolist(),
            "velocity": velocity_array.tolist(),
            "event": "none"
        }
        return dictionary

    def merge_vtk_data_in_points(self, base_grid: vtk.vtkImageData,
                                 pintel_data: list[vtk.vtkImageData]=[],
                                 vueron_data: list[vtk.vtkPolyData]=[],
                                 keti_data: vtk.vtkPolyData=None,
                                 total_num_data = 0, goal_pos=(0, 0), target_speed=1.1,
                                 merged_grid: vtk.vtkImageData=None):
        self.array = []
        # array_type = ['pos_x', 'pos_y', 'vel_x', 'vel_y', 'target_speed', 'goal_x', 'goal_y']

        if merged_grid is not None:
            grid_data = merged_grid
        else:
            grid_data = self.merge_vtk_data_in_grid(base_grid, pintel_data=pintel_data, keti_data=keti_data)

        dens_vtk = grid_data.GetCellData().GetArray("density")
        dens = vtk_to_numpy(dens_vtk)
        vel_vtk = grid_data.GetCellData().GetArray("velocity")
        vel = vtk_to_numpy(vel_vtk)
        # shape = (num_cells,)

        dx, dy, _ = grid_data.GetSpacing()
        cell_area = dx * dy
        counts = np.rint(dens * cell_area).astype(int)

        nx, ny, nz = grid_data.GetDimensions()  # point dimensions
        nx_cells, ny_cells = nx - 1, ny - 1
        origin = np.array(grid_data.GetOrigin())

        mask = (counts > 0)
        cell_indices = np.nonzero(mask)[0]

        js = cell_indices // nx_cells
        is_ = cell_indices % nx_cells

        all_pts = []
        for ci, i, j in zip(cell_indices, is_, js):
            n = counts[ci]
            uv = self._monte_carlo_cvt(n, samples=20000, iterations=3)

            cell_origin = origin[:2] + np.array([i * dx, j * dy])

            pts_world = cell_origin + uv * np.array([dx, dy])
            vel_tile = np.tile(vel[ci][:2], (pts_world.shape[0], 1))
            ts_gx_gy_tile = np.tile(np.array([target_speed, goal_pos[0], goal_pos[1]]), (pts_world.shape[0], 1))
            arr7 = np.hstack([pts_world, vel_tile, ts_gx_gy_tile])

            all_pts.append(arr7)

        for point_cloud in vueron_data:
            pts = vtk_to_numpy(point_cloud.GetPoints().GetData())[:, :2]
            vel = vtk_to_numpy(point_cloud.GetPointData().GetArray("velocity"))[:, :2]
            ts_gx_gy_tile = np.tile(np.array([target_speed, goal_pos[0], goal_pos[1]]), (pts.shape[0], 1))
            arr_n_7 = np.hstack([pts, vel, ts_gx_gy_tile])

            all_pts.append(arr_n_7)

        if not all_pts:
            self.array = np.empty((0, 7), dtype=np.float64)
            self.vtk_data = vtkPolyData()
            return self.vtk_data

        all_pts = np.vstack(all_pts)
        self.array = all_pts

        n = self.array.shape[0]
        points_xyz = np.hstack([self.array[:, 0:2], np.zeros((n, 1))]).astype(np.float32)
        vectors_xyz = np.hstack([self.array[:, 2:4], np.zeros((n, 1))]).astype(np.float32)

        points = vtkPoints()
        points.SetData(numpy_support.numpy_to_vtk(points_xyz))

        point_cloud = vtkPolyData()
        point_cloud.SetPoints(points)

        point_data = point_cloud.GetPointData()

        vtk_vectors = numpy_support.numpy_to_vtk(vectors_xyz)
        vtk_vectors.SetName("velocity")
        point_data.SetVectors(vtk_vectors)

        vtk_scalar_a = numpy_support.numpy_to_vtk(self.array[:, 4].astype(np.float32))
        vtk_scalar_a.SetName("target_speed")
        point_data.AddArray(vtk_scalar_a)

        vtk_scalar_b = numpy_support.numpy_to_vtk(self.array[:, 5].astype(np.float32))
        vtk_scalar_b.SetName("goal_x")
        point_data.AddArray(vtk_scalar_b)

        vtk_scalar_c = numpy_support.numpy_to_vtk(self.array[:, 6].astype(np.float32))
        vtk_scalar_c.SetName("goal_y")
        point_data.AddArray(vtk_scalar_c)

        glyph_filter = vtkVertexGlyphFilter()
        glyph_filter.SetInputData(point_cloud)
        glyph_filter.Update()

        vertex_cloud = glyph_filter.GetOutput()

        self.vtk_data = vertex_cloud
        return vertex_cloud

    def write_binary_file_for_e8(self, file_path):
        from .binary_editor import E8BinaryEditor
        editor = E8BinaryEditor()
        editor.data = self.array
        editor.write_binary_file(file_path)
        # editor.write_ascii_csv_file(file_path+'.csv')

    def _load_array_from_json(self, reader):
        if self.company == CompanyType.Pintel:
            data_list = reader.get('count_data')
            self.array = np.array(data_list)

        elif self.company == CompanyType.Vueron:
            people_dict_parent = reader.get('payload.clientFrames[0]')
            if 'vObjects' not in people_dict_parent:
                raise FileNotFoundError('no people data in Vueron')
            people_dict_list = people_dict_parent['vObjects']
            people_array = []
            for person_dict in people_dict_list:
                x, y = self.gps_to_korean(person_dict['latitude'], person_dict['longitude'])
                person_list = [x, y,
                               person_dict['velocityX'], person_dict['velocityY'],
                               person_dict['id'], person_dict['age']]
                people_array.append(person_list)
            self.array = np.array(people_array)

        elif self.company == CompanyType.KETI:
            # sensor_list = np.array(reader.get('result'))
            json_ext_1 = json.loads(reader.get('result_data'))
            sensor_list = json.loads(json_ext_1.get('result'))
            # sensor_list = np.array(json_ext_2.get('density'))

            arrays = []

            def convert_16_to_10(num_str):
                num_dict = { '0': 0,
                    '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
                    '6': 6, '7': 7, '8': 8, '9': 9, 'a': 10,
                    'b': 11, 'c': 12, 'd': 13, 'e': 14, 'f': 15}

                pos = 0
                num = 0
                for i in num_str[::-1]:
                    num += num_dict[i] * (16 ** pos)
                    pos += 1

                return num

            for sensor_dict in sensor_list:
                # id_str = sensor_dict['id']
                # id = convert_16_to_10(id_str[:2]+id_str[3:])
                id = sensor_dict['id']
                origin = sensor_dict['position']
                density_array = np.array(sensor_dict['density'])
                direction_array = np.array(sensor_dict['direction'])

                density_flat = density_array.flatten('C').reshape(-1, 1)
                # density_flat = density_array[::-1].flatten('C').reshape(-1, 1)  # Todo: 혹시 행 역순이면 이쪽으로...
                density_array.flatten()
                direction_flat = direction_array.reshape(-1, 2)

                id_array = np.array([[id] + origin,
                                     [density_array.shape[0], density_array.shape[1], 0]])
                dd_array = np.hstack([density_flat, direction_flat])

                labeled_array = np.vstack([id_array, dd_array])

                arrays.append(labeled_array)

            max_rows = max(arr.shape[0] for arr in arrays)
            cols = arrays[0].shape[1]

            padded = np.array([
                np.vstack([arr, np.full((max_rows - arr.shape[0], cols), np.nan)])
                for arr in arrays
            ])

            self.array = padded
        return self.array

    def _make_vtk_from_pintel(self):
        if self.array.size == 0:
            raise ValueError('[Pintel] no data')

        # print(self.array.shape)

        min_xy_max_xy = [self.array[:, 0].min(), self.array[:, 1].min(),
                         self.array[:, 0].max(), self.array[:, 1].max()]

        [x_min, y_min, x_max, y_max] = min_xy_max_xy

        spacing = 2
        nx = int((x_max - x_min) / spacing) + 1
        ny = int((y_max - y_min) / spacing) + 1

        ix = ((self.array[:, 0] - x_min) / spacing).astype(int)
        iy = ((self.array[:, 1] - y_min) / spacing).astype(int)

        flat_index = iy * nx + ix

        scalar_flat = np.full(ny * nx, np.nan, dtype=np.float32)
        scalar_flat[flat_index] = self.array[:, 2]

        ghost_array = np.zeros(scalar_flat.size, dtype=np.uint8)
        ghost_array[np.isnan(scalar_flat)] = 1

        no_nan_scalar = np.nan_to_num(scalar_flat, nan=0.0)
        vtk_array = numpy_support.numpy_to_vtk(no_nan_scalar, array_type=VTK_FLOAT)
        vtk_array.SetName("number of people")

        vtk_ghost = numpy_support.numpy_to_vtk(ghost_array, array_type=VTK_UNSIGNED_CHAR)
        vtk_ghost.SetName(vtkDataSetAttributes.GhostArrayName())

        image_data = vtkImageData()
        image_data.SetDimensions(nx + 1, ny + 1, 1)
        image_data.SetSpacing(spacing, spacing, 1.0)
        image_data.SetOrigin(x_min, y_min, 0.0)
        image_data.GetCellData().SetScalars(vtk_array)
        image_data.GetCellData().SetActiveScalars('number of people')
        image_data.GetCellData().AddArray(vtk_ghost)

        n = self.array.shape[0]
        vector_flat = np.full((ny * nx, 3), np.nan, dtype=np.float32)
        vectors_xyz = np.hstack([self.array[:, 3:], np.zeros((n, 1))]).astype(np.float32)
        vector_flat[flat_index] = vectors_xyz
        vector_flat = np.nan_to_num(vector_flat, nan=0.0)
        vtk_vectors = numpy_support.numpy_to_vtk(vector_flat)
        vtk_vectors.SetName("velocity")
        image_data.GetCellData().SetVectors(vtk_vectors)

        # print("Num Points:", image_data.GetNumberOfPoints())
        # print("Num Scalars:", vtk_array.GetNumberOfTuples())

        self.vtk_data = image_data
        return image_data

    def _make_vtk_from_vueron(self):
        n = self.array.shape[0]
        points_xyz = np.hstack([self.array[:, 0:2], np.zeros((n, 1))]).astype(np.float32)
        vectors_xyz = np.hstack([self.array[:, 2:4], np.zeros((n, 1))]).astype(np.float32)

        points = vtkPoints()
        points.SetData(numpy_support.numpy_to_vtk(points_xyz))

        point_cloud = vtkPolyData()
        point_cloud.SetPoints(points)

        point_data = point_cloud.GetPointData()

        vtk_vectors = numpy_support.numpy_to_vtk(vectors_xyz)
        vtk_vectors.SetName("velocity")
        point_data.SetVectors(vtk_vectors)

        vtk_scalar_a = numpy_support.numpy_to_vtk(self.array[:, 4].astype(np.float32))
        vtk_scalar_a.SetName("id")
        point_data.AddArray(vtk_scalar_a)

        vtk_scalar_b = numpy_support.numpy_to_vtk(self.array[:, 5].astype(np.float32))
        vtk_scalar_b.SetName("age")
        point_data.AddArray(vtk_scalar_b)

        glyph_filter = vtkVertexGlyphFilter()
        glyph_filter.SetInputData(point_cloud)
        glyph_filter.Update()

        vertex_cloud = glyph_filter.GetOutput()

        self.vtk_data = vertex_cloud
        return vertex_cloud

    def _make_vtk_from_keti(self):
        appender = vtkAppendPolyData()

        for labeled_array in self.array:
            labeled_array: np.ndarray
            # print(labeled_array)
            # >>>
            id = int(labeled_array[0,0])
            # ---
            # id_str = labeled_array[0,0]
            # id = int(id_str[:2] + id_str[3:], 16)
            # <<<
            origin = list(labeled_array[0,1:])
            shape = list(labeled_array[1,:2].astype(int))

            data_array_with_nan = labeled_array[2:]
            # >>>
            valid_rows = ~np.isnan(data_array_with_nan).any(axis=1)
            # valid_rows = ~np.isnan(data_array_with_nan.astype(float)).any(axis=1)
            # <<<

            data_array = data_array_with_nan[valid_rows]

            image_data = vtkImageData()
            image_data.SetDimensions(shape[0] + 1, shape[1] + 1, 1)
            image_data.SetSpacing(2, 2, 1.0)
            # >>> image_data.SetOrigin(origin[0], origin[1], 0.0)
            image_data.SetOrigin(float(origin[0]), float(origin[1]), 0.0)
            # <<<

            vtk_array = numpy_support.numpy_to_vtk(data_array[:, 0], array_type=VTK_FLOAT)
            vtk_array.SetName("density")
            image_data.GetCellData().SetScalars(vtk_array)

            n = data_array.shape[0]
            vtk_array = numpy_support.numpy_to_vtk(np.full((n, 1), id), array_type=VTK_FLOAT)
            vtk_array.SetName("id")
            image_data.GetCellData().AddArray(vtk_array)

            vectors_xyz = np.hstack([data_array[:, 1:], np.zeros((n, 1))]).astype(np.float32)
            vtk_vectors = numpy_support.numpy_to_vtk(vectors_xyz)
            vtk_vectors.SetName("direction")
            image_data.GetCellData().SetVectors(vtk_vectors)

            surface_filter = vtkDataSetSurfaceFilter()
            surface_filter.SetInputData(image_data)

            appender.AddInputConnection(surface_filter.GetOutputPort())

        appender.Update()

        merged_data = appender.GetOutput()

        self.vtk_data = merged_data
        return merged_data

    def _make_rainbow_lut(self):
        lut = vtk.vtkLookupTable()
        lut.SetNumberOfTableValues(64)
        lut.Build()

        ctf = vtk.vtkColorTransferFunction()
        ctf.SetColorSpaceToHSV()
        ctf.AddRGBPoint(0.0, 0.0, 0.0, 1.0)  # Blue
        ctf.AddRGBPoint(0.2, 0.0, 1.0, 1.0)  # Cyan
        ctf.AddRGBPoint(0.4, 0.0, 1.0, 0.0)  # Green
        ctf.AddRGBPoint(0.6, 1.0, 1.0, 0.0)  # Yellow
        ctf.AddRGBPoint(0.8, 1.0, 0.5, 0.0)  # Orange
        ctf.AddRGBPoint(1.0, 1.0, 0.0, 0.0)  # Red

        for i in range(64):
            t = 300.0 + 100.0 * (i / 64.0)
            r, g, b = ctf.GetColor((t - 300.0) / 100.0)
            lut.SetTableValue(i, r, g, b, 1.0)
        return lut

    def _do_average_array(self, array_list):
        stacked = np.stack(array_list, axis=0)
        mask = stacked > 0
        sum_vals = stacked.sum(axis=0)
        count_vals = mask.sum(axis=0)
        combined = np.zeros_like(sum_vals)
        np.divide(sum_vals, count_vals, out=combined, where=(count_vals > 0))
        return combined

    def _append_cell_data_to_image(self, base_grid, name:str, array: np.ndarray, nx, ny, flatten_transposed=False):
        if array.shape == (nx, ny):  # nx행 ny열 스칼라 배열일 때
            flatten_array = array.flatten(order='F')
        elif array.shape == (ny, nx):  # 전치되어 있을 때
            flatten_array = array.flatten(order='C')
        elif array.shape == (nx, ny, 3):  # nx행 ny열 벡터 배열일 때
            flatten_array = array.reshape(-1, 3, order='F')
        elif array.shape == (ny, nx, 3):  # 전치되어 있을 때
            flatten_array = array.reshape(-1, 3, order='C')
        elif array.shape == (nx*ny,):  # nx행 ny열인데 flatten된 스칼라 배열
            if flatten_transposed:
                array_2d = array.reshape(ny, nx)
                flatten_array = array_2d.flatten(order='C')
            else:
                flatten_array = array
        elif array.shape == (nx*ny, 3):  # nx행 ny열인데 flatten된 벡터 배열
            flatten_array = array
        else:
            raise TypeError('Unsupported shape')

        vtk_array = numpy_support.numpy_to_vtk(num_array=flatten_array)
        vtk_array.SetName(name)
        base_grid.GetCellData().AddArray(vtk_array)

    def _monte_carlo_cvt(self, n_generators, samples=10000, iterations=30):
        gens = np.random.rand(n_generators, 2)
        for _ in range(iterations):
            pts = np.random.rand(samples, 2)
            # 거리 계산 및 가장 가까운 생성점 할당
            d2 = ((pts[:, None, :] - gens[None, :, :]) ** 2).sum(axis=2)
            nearest = np.argmin(d2, axis=1)
            new_gens = np.zeros_like(gens)
            for i in range(n_generators):
                mask = (nearest == i)
                if np.any(mask):
                    new_gens[i] = pts[mask].mean(axis=0)
                else:
                    new_gens[i] = gens[i]
            gens = new_gens
        return gens
