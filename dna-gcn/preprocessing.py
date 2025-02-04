import numpy as np
import h5py
import itertools
import time

def weight():
    weight_vector = [0] * 98
    for i in range(2, 100):
        weight_vector[i] = np.exp(-np.abs((i + 0.5) - 51) / 2)
    return np.array(weight_vector)

def transform_one_hot_X_into_kmer_frequences(one_hot_X, kmer_len, slide_window):
    base_list = ['A', 'C', 'G', 'T']
    kmers_list = [''.join(item) for item in itertools.product(base_list, repeat=kmer_len)]

    kmer_id_dict = {}
    for i in range(len(kmers_list)):
        kmer_id_dict[kmers_list[i]] = i

    frenquces_array = np.zeros((one_hot_X.shape[0], len(kmers_list)))
    slide_frequence_array = np.zeros((one_hot_X.shape[0] * (one_hot_X.shape[1] - slide_window + 1), len(kmers_list)))

    n = 0
    for i in range(one_hot_X.shape[0]):
        x = one_hot_X[i, :, :]
        s = ''.join([base_list[np.argmax(x[j])] for j in range(x.shape[0])])
        for start_index in range(len(s) - kmer_len + 1):
            this_kmer = s[start_index:start_index + kmer_len]
            frenquces_array[i, kmer_id_dict[this_kmer]] += 1
        for j in range(len(s) - slide_window + 1):
            s1 = s[j:(j + slide_window)]
            for k in range(slide_window - kmer_len + 1):
                that_kmer = s1[k:(kmer_len + k)]
                slide_frequence_array[n * (len(s) - slide_window + 1) + j, kmer_id_dict[that_kmer]] += 1
        n += 1
    return frenquces_array, slide_frequence_array


def load_data(dataset):
    data = h5py.File(dataset, 'r')
    sequence_code = data['sequences'].value
    label = data['labs'].value
    label = np.array(label).reshape(len(label), 1)
    return sequence_code, label


def data_preprocessing(train_dataset, test_dataset, kmer_len, slide_window):
    t = time.time()
    train_data, train_label = load_data(train_dataset)
    test_data, test_label = load_data(test_dataset)
    train_frequence_array, train_slide_frequence_array = transform_one_hot_X_into_kmer_frequences(train_data, kmer_len,
                                                                                                  slide_window)
    test_frequence_array, test_slide_frequence_array = transform_one_hot_X_into_kmer_frequences(test_data, kmer_len,
                                                                                                slide_window)
    frequence_array = np.vstack((train_frequence_array, test_frequence_array))
    total_slide_frequence_array = np.vstack((train_slide_frequence_array, test_slide_frequence_array))
    total_raw_label = np.vstack((train_label, test_label))
    count = (frequence_array != 0).sum(0)
    slide_count = (total_slide_frequence_array != 0).sum(0)

    a, b = total_slide_frequence_array.shape[0], total_slide_frequence_array.shape[1]
    w = np.zeros((b, b))
    for i in range(b):
        for j in range(i + 1, b):
            w[i, j] = np.sum((total_slide_frequence_array[:, i] > 0) & (total_slide_frequence_array[:, j] > 0))
            w[j, i] = w[i, j]
    '''
    for i in range(b):
        for j in range(i + 1, b):
            for k in range(frequence_array.shape[0]):
                ref_matrix = total_slide_frequence_array[(k * (101 - slide_window + 1)):((k+1) * (101 - slide_window + 1))]
                if np.sum((ref_matrix[:, i] > 0) & (ref_matrix[:, j] > 0)) > 0:
                    w[i, j] = w[i, j] + 1
            w[j, i] = w[i, j]
    w = w / (frequence_array.shape[0])
    '''
    p = slide_count / a  # p为一维数组
    a1 = frequence_array.shape[0]
    b1 = frequence_array.shape[1]
    '''
    A1 = np.identity(a1)
    frequence_array[frequence_array > 0] = 1
    A2 = frequence_array
    A3 = np.transpose(A2)
    A4 = w
    '''
    A1 = np.identity(a1)
    A4 = np.identity(b1)
    A2 = frequence_array * (np.ones(a1).reshape(a1, 1) * np.log(a1 / (1 + count)))
    A3 = np.transpose(A2)
    p_ = p.reshape(len(p), 1) * p
    A4[w > 0] = np.log(w[w > 0] / p_[w > 0])
    A4[A4 < 0] = 0
    A4 = A4 - np.diag(np.diag(A4)) + np.identity(A4.shape[0])

    A = np.vstack((np.hstack((A1, A2)), np.hstack((A3, A4))))
    D = np.linalg.inv(np.diag(np.sqrt(np.sum(A, axis=1))))
    A_ = np.dot(np.dot(D, A), D)
    label = np.vstack((total_raw_label, np.array([0] * (frequence_array.shape[1])).reshape(frequence_array.shape[1], 1)))
    print(time.time() - t)
    return A, A_, train_label, label, train_frequence_array, test_frequence_array, train_slide_frequence_array, total_slide_frequence_array


