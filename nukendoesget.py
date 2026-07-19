# -*- coding: UTF-8 -*-
# Copyright 2026 LIUXIAOBO (刘晓波)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import nuke

def getcurnodes():
    global selectedndoes_nodesnameslsit_get
    nodes = nuke.selectedNodes()
    nodesnameslsit = [i.fullName() for i in nodes]
    nodesclasslsit = sorted(set([i.Class() for i in nodes]))
    print(nodesnameslsit,nodesclasslsit)
    return nodesnameslsit,nodesclasslsit