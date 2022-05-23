import json
import pandas as pd
import numpy as np


with open("results.json") as json_file:
    data = json.load(json_file)

problems = list(data.values())
methods = list(data.keys())
cols = list(problems[0].keys())
metrics = ["wallclock_time", "problems_solved", "average_constraints_in_any_problem"]
cols = [c + " " + m for c in cols for m in metrics]
problem_dict = pd.DataFrame(columns=cols)

for method, method_results in data.items():
    method_dict = {}
    for r, m in method_results.items():
        method_dict["method"] = method
        for met in metrics:
            try:
                if isinstance(m[met], float) is True:
                    method_dict[r + " " + met] = np.round(m[met], 3)
                else:
                    method_dict[r + " " + met] = m[met]
            except KeyError:
                method_dict[r + " " + met] = "N/A"
    problem_dict = problem_dict.append(method_dict, ignore_index=True)


names = ["reactor", "supply", "heat_exchange", "toy"]
problem_dfs = []
for n in names:
    col_names = ["method"]
    for c in cols:
        if n in c:
            col_names.append(c)

    problem_dfs.append(problem_dict.filter(col_names))


for i in range(len(names)):
    df = problem_dfs[i]
    m_list = []
    n_list = []
    res = []
    flag = False
    for m in metrics:
        cols = df.columns
        for c in cols:
            # print(m,c1)
            if m in c:
                try:
                    n = int(c.split(" ")[0].split("_")[-1])
                except ValueError:
                    n = c.split(" ")[0].split("_")[-1]
                if isinstance(n, int) is False:
                    n_list.append("")
                else:
                    n_list.append(n)
                    flag = True
                m_list.append(m)
                res.append(df[c])
    if flag is True:
        res = np.array(res).T
        tuples = list(zip(m_list, n_list))
        index = pd.MultiIndex.from_tuples(tuples)
        problem_dfs[i] = pd.DataFrame(res, index=methods, columns=index)
        print(problem_dfs[i].to_latex(index=True))
    else:
        res = np.array(res).T
        problem_dfs[i] = pd.DataFrame(res, index=methods, columns=m_list)
        print(problem_dfs[i].to_latex(index=True))
