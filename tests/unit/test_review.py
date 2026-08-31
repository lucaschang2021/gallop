from datetime import date

from gallop.core.review import review_dates


def test_review_dates_preserve_t1_t7_t30():
    assert review_dates(date(2026, 1, 1)) == {
        "T+1": "2026-01-02",
        "T+7": "2026-01-08",
        "T+30": "2026-01-31",
    }
