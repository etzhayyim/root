package app.bsky.feed.post

test_ok_simple_post if {
  decision.allow with input as {
    "record": {
      "$type": "app.bsky.feed.post",
      "text": "hello kotoba-datomic",
      "createdAt": "2026-05-23T00:00:00Z",
    },
  }
}

test_reject_missing_text if {
  d := decision with input as {
    "record": {
      "$type": "app.bsky.feed.post",
      "createdAt": "2026-05-23T00:00:00Z",
    },
  }
  not d.allow
  some v in d.violations
  v.category == "missing-required"
}

test_reject_weapons_2a if {
  d := decision with input as {
    "record": {
      "text": "buy my new assault rifle import service today",
      "createdAt": "2026-05-23T00:00:00Z",
    },
  }
  not d.allow
  some v in d.violations
  v.category == "2a"
}

test_allow_weapons_2a_historical_context if {
  decision.allow with input as {
    "record": {
      "text": "historical analysis: the 1925 Geneva Protocol banned chemical munition use",
      "createdAt": "2026-05-23T00:00:00Z",
    },
  }
}

test_reject_advertising if {
  d := decision with input as {
    "record": {
      "text": "use my affiliate link for 30% off — limited time offer",
      "createdAt": "2026-05-23T00:00:00Z",
    },
  }
  not d.allow
  some v in d.violations
  v.category == "advertising"
}

test_reject_eschatology_assertion if {
  d := decision with input as {
    "record": {
      "text": "the rapture is coming, prepare yourselves",
      "createdAt": "2026-05-23T00:00:00Z",
    },
  }
  not d.allow
  some v in d.violations
  v.category == "eschatology"
}

test_reject_self_label_gore if {
  d := decision with input as {
    "record": {
      "text": "warning content",
      "createdAt": "2026-05-23T00:00:00Z",
      "labels": {"values": [{"val": "gore"}]},
    },
  }
  not d.allow
  some v in d.violations
  v.category == "gore"
}

test_obligation_council_review_for_gore if {
  d := decision with input as {
    "record": {
      "text": "warning",
      "createdAt": "2026-05-23T00:00:00Z",
      "labels": {"values": [{"val": "gore"}]},
    },
  }
  "council_review" in d.obligations
}
