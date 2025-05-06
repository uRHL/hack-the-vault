import htv

class TestConf:
    init_values = dict(k1=1, k2=2, k3=3)

    def test_init(self):
        print(1, htv.CONF)
        assert len(htv.CONF) == 1

    def test_remove_non_existent(self):
        htv.CONF.remove_values(*self.init_values.keys())
        print(2, htv.CONF)
        assert len(htv.CONF) == 1

    def test_update_values(self):
        htv.CONF.update_values(**self.init_values)
        print(3, htv.CONF)
        assert len(htv.CONF) == 4

    def test_remove_existent(self):
        htv.CONF.remove_values(list(self.init_values.keys())[0])
        print(4, htv.CONF)
        assert len(htv.CONF) == 3

    def test_reset(self):
        htv.CONF.reset()
        print(5, htv.CONF)
        assert len(htv.CONF) == 1
