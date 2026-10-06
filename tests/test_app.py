from streamlit.testing.v1 import AppTest
from interceptiq.simulation import ROOT

def test_public_demo():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
    assert not app.exception and len(app.metric)==2
    app.radio[0].set_value('Normal flow').run()
    assert not app.exception
    app.slider[0].set_value(.8).run()
    assert not app.exception
