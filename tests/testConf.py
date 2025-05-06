import htk

class TestConf:
    init_values = dict(k1=1, k2=2, k3=3)

    def test_init(self):
        print(1, htk.CONF)
        assert len(htk.CONF) == 1

    def test_remove_non_existent(self):
        htk.CONF.remove_values(*self.init_values.keys())
        print(2, htk.CONF)
        assert len(htk.CONF) == 1

    def test_update_values(self):
        htk.CONF.update_values(**self.init_values)
        print(3, htk.CONF)
        assert len(htk.CONF) == 4

    def test_remove_existent(self):
        htk.CONF.remove_values(list(self.init_values.keys())[0])
        print(4, htk.CONF)
        assert len(htk.CONF) == 3

    def test_reset(self):
        htk.CONF.reset()
        print(5, htk.CONF)
        assert len(htk.CONF) == 1
