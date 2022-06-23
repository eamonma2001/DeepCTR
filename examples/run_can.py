import numpy as np

from deepctr.models import CAN
from deepctr.feature_column import SparseFeat, VarLenSparseFeat, DenseFeat, get_feature_names


def get_xy_fd():
    feature_columns = [SparseFeat('user', 3, embedding_dim=10),
                       SparseFeat('gender', 2, embedding_dim=4),
                       # target emb size: sum([w[0] * w[1] for w in can_config['target_emb_w']]) + sum(can_config['target_emb_b'])
                       SparseFeat('item_id', 3 + 1, embedding_dim=160),
                       SparseFeat('cate_id', 2 + 1, embedding_dim=160), DenseFeat('pay_score', 1)]
    feature_columns += [
        # hist pref seq emb size : can_config['target_emb_w'][0][0],
        VarLenSparseFeat(SparseFeat('hist_item_id', vocabulary_size=3 + 1, embedding_dim=16),
                         maxlen=4, length_name="seq_length"),
        VarLenSparseFeat(SparseFeat('hist_cate_id', 2 + 1, embedding_dim=16), maxlen=4,
                         length_name="seq_length")]
    # Notice: History behavior sequence feature name must start with "hist_".
    behavior_feature_list = ["item_id", "cate_id"]
    uid = np.array([0, 1, 2])
    ugender = np.array([0, 1, 0])
    iid = np.array([1, 2, 3])  # 0 is mask value
    cate_id = np.array([1, 2, 2])  # 0 is mask value
    pay_score = np.array([0.1, 0.2, 0.3])

    hist_iid = np.array([[1, 2, 3, 0], [3, 2, 1, 0], [1, 2, 0, 0]])
    hist_cate_id = np.array([[1, 2, 2, 0], [2, 2, 1, 0], [1, 2, 0, 0]])
    seq_length = np.array([3, 3, 2])  # the actual length of the behavior sequence

    feature_dict = {'user': uid, 'gender': ugender, 'item_id': iid, 'cate_id': cate_id,
                    'hist_item_id': hist_iid, 'hist_cate_id': hist_cate_id,
                    'pay_score': pay_score, 'seq_length': seq_length}
    x = {name: feature_dict[name] for name in get_feature_names(feature_columns)}
    y = np.array([1, 0, 1])
    return x, y, feature_columns, behavior_feature_list


if __name__ == "__main__":
    x, y, feature_columns, behavior_feature_list = get_xy_fd()

    co_action_config = [
        {
            'name': 'co_action_for_item',
            'target': 'item_id',  # target emb need to reshape
            'pref_seq': ['hist_item_id', ],  # seq emb need to co-action
            'co_action_conf': {
                'target_emb_w': [[16, 8], [8, 4]],
                'target_emb_b': [0, 0],
                'indep_action': False,
                'orders': 3,  # exp non_linear trans
            }
        },
        {
            'name': 'co_action_for_cate',
            'target': 'cate_id',
            'pref_seq': ['hist_cate_id', ],
            'co_action_conf': {
                'target_emb_w': [[16, 8], [8, 4]],
                'target_emb_b': [0, 0],
                'indep_action': False,
                'orders': 3,  # exp non_linear trans
            }
        }
    ]

    model = CAN(feature_columns, co_action_config=co_action_config)
    model.compile('adam', 'binary_crossentropy',
                  metrics=['binary_crossentropy'])
    history = model.fit(x, y, verbose=1, epochs=10, validation_split=0.5)
