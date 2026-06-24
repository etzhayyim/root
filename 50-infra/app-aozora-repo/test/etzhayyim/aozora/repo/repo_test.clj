(ns etzhayyim.aozora.repo.repo-test
  "app-aozora-repo round-trip + **spec conformance** tests.

  The golden CIDs below are the output of go-ipfs 0.41
  `ipfs dag put --store-codec dag-cbor --input-codec dag-json` — i.e. the
  canonical IPLD/AT-Proto dag-cbor encoding. Our pure-clj encoder MUST reproduce
  them byte-for-byte, which proves the repo's record/MST block CIDs are
  spec-exact (resolving ADR-2606242330 staged #2) while every block lives on the
  kotoba Datom log (never an @atproto/repo side store)."
  (:require [clojure.test :refer [deftest is testing]]
            [etzhayyim.aozora.repo.dag-cbor :as dc]
            [etzhayyim.aozora.repo.cid :as cid]
            [etzhayyim.aozora.repo.blockstore :as bs]
            [etzhayyim.aozora.repo.repo :as repo]))

(def LINK "bafyreigbtj4x7ip5legnfznufuopl4sg4knzc2cof6duas4b3q2fy6swua")

(def golden
  [[{}                            "bafyreigbtj4x7ip5legnfznufuopl4sg4knzc2cof6duas4b3q2fy6swua"]
   [{"hello" "world"}             "bafyreidykglsfhoixmivffc5uwhcgshx4j465xwqntbmu43nb2dzqwfvae"]
   [{"a" 1 "b" [1 2 3] "c" "x"}   "bafyreictq7pos2d7eojp3rxickyoze54vyuqve3pnzh4xst2hxwgysyi2y"]
   [{"b" 1 "aa" 2}                "bafyreihbaf6v4gjeo76rl6ncekrny5lwbgyjf7zdw2m7w77xsjm3xvige4"]
   [{"n" 1000000}                 "bafyreifqaeztvcbhkv4lhj33icfaijuvgdevkso32rvbcb3afqykj2go3m"]
   [{"neg" -5}                    "bafyreidpfrdxdvxffhglvwu4k7t6wro67iupz3ayd7kx4jebajztp34ste"]
   [{"t" true "f" false "z" nil}  "bafyreiav3swgy5ly4z3syqvho6nbjjaaaixpokht7ppthbqzeogjron22i"]
   [{"a" [] "o" {}}               "bafyreiavkoi2co2wuu34omkcarzrghf3gpqa656w76sw6ueael37faw2ym"]
   [{"x" {"y" "z"}}               "bafyreigzomyi3sc5k7v7ji3jizadwxmjxdlrlcjbw5ikd5gasd5yslae4e"]])

(deftest dag-cbor-spec-exact-cids
  (testing "CIDv1(dag-cbor) byte-identical to `ipfs dag put`"
    (doseq [[v expected] golden]
      (is (= expected (cid/cid-of v)) (str "cid of " (pr-str v))))))

(deftest cid-link-tag42
  (testing "a CID link encodes as CBOR tag 42 (matches ipfs dag-json `{/: cid}`)"
    (is (= "bafyreic5qoj6qotw7hop4mnfgj6oxng33jhnf6zl2jhxuitux4sggnqnaa"
           (cid/cid-of {"l" (dc/cid-link LINK)})))))

(deftest dag-cbor-determinism
  (testing "source map key order does not change the CID (canonical sort)"
    (is (= (cid/cid-of {"a" 1 "b" 2 "c" 3})
           (cid/cid-of (array-map "c" 3 "a" 1 "b" 2)))))
  (testing "floats are rejected (AT Proto records disallow them)"
    (is (thrown? clojure.lang.ExceptionInfo (dc/encode {"f" 1.5})))))

(deftest blockstore-on-datom-log
  (let [store (bs/->mem-blockstore)
        {:keys [cid bytes]} (cid/block {"hello" "world"})]
    (testing "put/get/has over the kotoba Datom log"
      (bs/put-block store cid bytes)
      (is (bs/has-block? store cid))
      (is (= (seq bytes) (seq (bs/get-block store cid))))
      (is (= 1 (bs/block-count store))))
    (testing "blocks are content-addressed Datoms (not a parallel store)"
      (is (some (fn [[e a _]] (and (= e cid) (= a :block/bytes))) (bs/datoms store))))
    (testing "repo head pointer lives on the same log"
      (bs/set-head! store "did:web:alice.etzhayyim.com" cid)
      (is (= cid (bs/get-head store "did:web:alice.etzhayyim.com"))))))

(deftest repo-put-record
  (let [store (bs/->mem-blockstore)
        did "did:web:alice.etzhayyim.com"
        coll "app.bsky.feed.post"
        rec {"text" "shalom" "createdAt" "2026-06-24T00:00:00Z"}
        {:keys [uri cid]} (repo/put-record store did coll "self" rec)]
    (testing "record stored as a spec-CID dag-cbor block on kotoba"
      (is (= "at://did:web:alice.etzhayyim.com/app.bsky.feed.post/self" uri))
      (is (= cid (cid/cid-of rec)))
      (is (bs/has-block? store cid)))
    (testing "EAVT projection makes it datalog-queryable on the same log"
      (is (= cid (bs/read-attr store uri :record/cid)))
      (is (= did (bs/read-attr store uri :record/did)))
      (is (= coll (bs/read-attr store uri :record/collection))))
    (testing "$link refs lift to tag-42 CID links (blob-safe addressing)"
      (is (= (repo/record-cid {"img" {"$link" LINK}})
             (cid/cid-of {"img" (dc/cid-link LINK)}))))))

(deftest commit-object
  (let [c (repo/format-commit {:did "did:web:alice.etzhayyim.com"
                               :data-cid LINK :rev "3jzfcijpj2z2a" :prev nil})]
    (testing "unsigned AT-Proto v3 commit is a stable dag-cbor block"
      (is (= 3 (get (:unsigned c) "version")))
      (is (string? (:cid c)))
      (is (= (:cid c) (cid/cid-of (:unsigned c)))))))
