from urllib.parse import parse_qsl
import numpy as np


def integrate(x=None, y=None, h=None):
    result = [0.] * len(y)
    if h:
        assert h > 0, 'h <= 0'
        for i in range(len(y) - 1):
            result[i+1] = result[i] + (y[i + 1] + y[i]) * h / 2
    elif x:
        assert len(x) == len(y), 'x and y must have the same length'
        for i in range(len(y) - 1):
            result[i+1] = result[i] + (y[i + 1] + y[i]) * (x[i + 1] - x[i]) / 2
    else:
        raise WrongArgumentsError('must got y or h')
    return result


class Data:
    """Abstract class for data parsers
    all parsers must have these attributes"""
    def __init__(self):
        self.exp_type = 'example_experiment'
        self.cols = [{'name': 'x_example',
                      'values': [1, 3, 5, 7, 9],
                      'type': 'X'},
                     {'name': 'y_example',
                      'values': [2, 4, 6, 8, 10],
                      'comment': 'example_comment',
                      'type': 'X'}]

    def __str__(self):
        return str({'exp_type': self.exp_type,
                    'columns': [{'name': col.get('name', ''),
                                 'comment': col.get('comment', ''),
                                 'type': col.get('type', 'Y')}
                                for col in self.cols]})

    def __repr__(self):
        return str({'exp_type': self.exp_type,
                    'columns': self.cols})


class CorrtestData(Data):
    def __init__(self, path_to_file):
        super().__init__()

        NAMES_IDX = 24 - 1
        DATA_START_IDX = 26 - 1
        EXP_PARAMS_IDX = 5 - 1

        self.filename = path_to_file.split('/')[-1]

        with open(path_to_file) as f:
            lines = [line.strip() for line in f]

        for name, value in parse_qsl(lines[EXP_PARAMS_IDX].split(':', maxsplit=1)[-1]):
            self.__setattr__(name, value)

        self.values = {name[0].upper(): [] for name in lines[NAMES_IDX].split()}
        for line in lines[DATA_START_IDX:]:
            for val, name in zip(line.split(), self.values):
                self.values[name].append(float(val))

        self.values['Q'] = integrate(y=self.values['I'], x=self.values['T'])

        if self.ExpType == 'ID_PotStatic':
            self.exp_type = 'CA'
            self.cols = [{'name': 'time, s',
                          'values': self.values['T'],
                          'type': 'X'
                          },
                         {'name': 'I, A',
                          'values': self.values['I'],
                          'comment': f"E={self.AppliedPotential}V Q={self.values['Q'][-1]:.3}C"
                          }]

        elif self.ExpType == 'ID_PotSquareWave':
            self.exp_type = 'PotStairStep'
            self.cols = [{'name': 'time, s',
                          'values': self.values['T'],
                          'type': 'X'
                          },
                         {'name': 'E, V',
                          'values': self.values['E']
                          },
                         {'name': 'I, A',
                          'values': self.values['I']}]

        elif self.ExpType == 'ID_PotDynamic':
            self.exp_type = 'Tafel'
            self.cols = [{'name': 'I, A',
                          'values': self.values['I']
                          },
                         {'name': 'lg(I)',
                          'values': np.log10(np.abs(self.values['I'])),
                          'type': 'X'
                          },
                         {'name': 'E, V',
                          'values': self.values['E'],
                          'comment': f"dE/dt={self.ScanRate}"
                          }]

        elif self.ExpType == 'ID_LSVStripping':
            self.exp_type = 'LinearStripping'

            deposition_final_idx = 0
            while self.values['T'][deposition_final_idx] < float(self.DepositionTime):
                deposition_final_idx += 1

            self.cols = [{'name': 'time, s',
                          'values': self.values['T'],
                          'type': 'X'
                          },
                         {'name': 'I, A',
                          'values': self.values['I'][:deposition_final_idx],
                          'comment': f"Deposition E={self.DepositionE}V Q={self.values['Q'][deposition_final_idx]:.3}C"
                          },
                         {'name': 'E, V',
                          'values': self.values['E'][deposition_final_idx:],
                          'type': 'X'
                          },
                         {'name': 'I, A',
                          'values': self.values['I'][deposition_final_idx:],
                          'comment': f"Stripping Q={self.values['Q'][-1] - self.values['Q'][deposition_final_idx]:.3}C"
                          }]

        elif self.ExpType == 'ID_OCP':
            self.exp_type = 'OCV'
            self.cols = [{'name': 'time, s',
                          'values': self.values['T'],
                          'type': 'X'
                          },
                         {'name': 'E, V',
                          'values': self.values['E']
                          }]

        elif self.ExpType == 'ID_GalStatic':
            self.exp_type = 'CP'
            self.cols = [{'name': 'time, s',
                          'values': self.values['T'],
                          'type': 'X'
                          },
                         {'name': 'E, V',
                          'values': self.values['E'],
                          'comment': f"I={self.PorCurr}V Q={self.values['Q'][-1]:.3}C"
                          }]

        elif self.ExpType == 'ID_LSVA':
            self.exp_type = 'LSV'
            self.cols = [{'name': 'E, V',
                          'values': self.values['E'],
                          'type': 'X'
                          },
                         {'name': 'I, A',
                          'values': self.values['I'],
                          'comment': f"dE/dt={self.ScanRate}"
                          },
                         {'name': 'Q, C',
                          'values': self.values['Q'],
                          'comment': f"dE/dt={self.ScanRate}"
                          }]

        elif self.ExpType == 'ID_CV':
            self.exp_type = 'CV'
            self.cols = [{'name': 'E, V',
                          'values': self.values['E'],
                          'type': 'X'
                          },
                         {'name': 'I, A',
                          'values': self.values['I'],
                          'comment': f'dE/dt={self.ScanRate}'
                          },
                         {'name': 'Q, C',
                          'values': self.values['Q'],
                          'comment': f'dE/dt={self.ScanRate}'
                          }]

            cycles_idx = [0] + \
                         [idx - DATA_START_IDX
                          for idx, line in enumerate(lines) if ' CYCLE' in line] + \
                         [len(self.values['I'])]

            for cycle in range(1, len(cycles_idx)):
                I = self.values['I'][cycles_idx[cycle - 1]:cycles_idx[cycle]]
                Q = integrate(y=I, h=1/float(self.Frq))

                self.cols.append({'name': 'I, A',
                                  'values': ['--'] * cycles_idx[cycle - 1] + I,
                                  'comment': f"Cycle {cycle}"})

                self.cols.append({'name': 'Q, C',
                                  'values': ['--'] * cycles_idx[cycle - 1] + Q,
                                  'comment': f"Cycle {cycle}"})
