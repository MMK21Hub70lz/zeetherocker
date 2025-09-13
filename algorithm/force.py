
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
df_news = pd.read_table('Agarose gel.txt',sep='	',header = None)
plt.plot(df_news[0],df_news[1],'-o', lw=3, color='royalblue',label='$G^{II}$')
#plt.xscale('log')
plt.xlabel('Time(s)')
plt.ylabel('Force(nN)')
plt.show()

'''
输入只有Agarose gel.txt
在sigma位置输出
'''