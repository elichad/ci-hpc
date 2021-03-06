#!/usr/bin/python
# author: Jan Hybs


from artifacts.collect.modules import CollectResult, CIHPCReport, AbstractCollectModule


class CollectModule(AbstractCollectModule):
    """
    This module excepts a dictionary as a first and only argument to the
    method process

    It simply merges system wide information and given object together
    Assuming the structure of the output report:
    {
        system:     { ... }
        problem:    { ... }
        result:     { ... }
        git:        { ... }
        timers:     [ { ... }, { ... }, ... ]
        libs:       [ { ... }, { ... }, ... ]
    }

    we are expecting the fields 'problem', 'result' and 'timers' to be given
    fields 'system' and 'git' are automatically obtained
    field  'libs' is optional

    Simple report file foo.json can look like this:
        {
         "problem": {
          "application": "bench-stat"
         },
         "result": {
          "duration": 12.697114944458
         },
         "timers": [
          {
           "duration": 1.48340058326721,
           "name": "mem_l1"
          },
          {
           "duration": 3.48957252502441,
           "name": "mem_l2"
          },
          {
           "duration": 7.72413110733032,
           "name": "mem_l3"
          }
         ]
        }

    """
    def process(self, object):
        report = CIHPCReport()
        report.merge(object)

        print(report)

        return CollectResult([report])
