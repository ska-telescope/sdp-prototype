import os

ms_files = [file for file in os.listdir(".") if file.endswith(".ms")]
latest_ms = max(ms_files, key=os.path.getctime)
print(latest_ms)

tb.open(latest_ms)
print('Measurement set: {}'.format(latest_ms))
print('* No. rows: {}'.format(tb.nrows()))
ant1 = tb.getcol('ANTENNA1')
ant2 = tb.getcol('ANTENNA2')
data = tb.getcol('DATA')
print('')
print('* Data  (Row id: ant1 - ant2 : Stokes I amplitude)')
for i in range(50):
    print('{:04d}: {} - {} : {:.6f}'.format(i, ant1[i], ant2[i],
                                    data[0, 0, i]))
tb.close()
