from pathlib import Path
from vtkmodules.vtkIOLegacy import vtkDataSetReader

from Lib.Converter.vtk_json_converter import VtkJsonConverter, CompanyType


def pintel(converter):  # 속도 측정하려고 나눠놨습니다. 굳이 함수 만들 필요 없어요
    converter.set_data_company(CompanyType.Pintel)
    converter.load_array_from_json_file(Path('./vtk_json_converter/XNP-C9253R_27278406.json'))
    vtk_data = converter.make_vtk()
    actor = converter.get_vtk_actor()  # actor가 필요할 때 --아직 미구현
    converter.write_vtk_file('test_pintel.vtk')  # 파일이 필요할 때

def vueron(converter):
    converter.set_data_company(CompanyType.Vueron)
    converter.load_array_from_json_file(Path('./vtk_json_converter/vueron.json'))
    converter.make_vtk()
    converter.write_vtk_file('test_vueron.vtk')

def keti(converter):
    converter.set_data_company(CompanyType.KETI)
    # converter.load_array_from_json_file(Path('./vtk_json_converter/keti.json'))
    converter.load_array_from_json_file(Path('C:\\Users\\nextfoam-CV-user\\AppData\\Local\\NEXTfoam\\DataHub\\v1.2\\received_data\\keti\\0001_20250524_053019588.json'))
    converter.make_vtk()
    converter.write_vtk_file('test_keti.vtk')

def merge1(converter, base_grid):
    converter.merge_vtk_data_in_grid(base_grid, pintel_data=[data1], vueron_data=[data2], keti_data=data3)
    dict_for_json = converter.make_json_dict_for_keti('001010101')
    converter.write_vtk_file('test_total.vtk')

def merge2(converter, base_grid):
    converter.merge_vtk_data_in_points(base_grid, pintel_data=[data1], vueron_data=[data2], keti_data=data3,
                                       total_num_data=2000)
    converter.write_binary_file_for_e8('test_total.e8b')


if __name__ == "__main__":
    converter = VtkJsonConverter()  # 컨버터 초기화 하는게 시간 제일 오래걸립니다. 최초 1회만 생성하세요
    # pintel(converter)
    # data1 = converter.get_vtk_data()
    # actor1 = converter.get_vtk_actor()
    #
    # vueron(converter)
    # data2 = converter.get_vtk_data()
    # actor2 = converter.get_vtk_actor()

    keti(converter)
    data3 = converter.get_vtk_data()
    # actor3 = converter.get_vtk_actor()
    #
    # reader = vtkDataSetReader()
    # reader.SetFileName('./vtk_json_converter/grid.vtk')
    # reader.Update()
    # base_grid = reader.GetOutput()
    # merge1(converter, base_grid)
    # merge2(converter, base_grid)
    # actor4 = converter.get_vtk_actor()

    # ==== 여기 아래부터는 시각화 테스트 ====

    # from vtk_json_converter.rendering_widget_for_test.rendering_dock import RenderingView
    # from vtkmodules.vtkIOLegacy import vtkUnstructuredGridReader, vtkDataSetReader
    # from vtkmodules.vtkRenderingCore import vtkDataSetMapper, vtkActor
    # from PySide6.QtWidgets import QApplication
    #
    # app = QApplication([])
    # window = RenderingView()
    # window.resize(800, 600)
    # window.show()
    #
    # reader = vtkUnstructuredGridReader()
    # reader.SetFileName('./vtk_json_converter/fense2.vtk')
    # mapper = vtkDataSetMapper()
    # mapper.SetInputConnection(reader.GetOutputPort())
    # actor = vtkActor()
    # actor.SetMapper(mapper)
    #
    # reader = vtkDataSetReader()
    # reader.SetFileName('./vtk_json_converter/grid_lines.vtk')
    # mapper = vtkDataSetMapper()
    # mapper.SetInputConnection(reader.GetOutputPort())
    # actor5 = vtkActor()
    # actor5.SetMapper(mapper)
    #
    # window.addActor(actor)
    # window.addActor(actor1)
    # window.addActor(actor2)
    # window.addActor(actor3)
    # window.addActor(actor4)
    # window.addActor(actor5)
    #
    # camera = window.view().renderer().GetActiveCamera()
    # camera.SetClippingRange(1, 1e9)
    #
    # window.refresh()
    # window.fitCamera()
    #
    # app.exec()
    #

