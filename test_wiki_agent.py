import unittest

from wiki_agent import Article, ResearchError, TopicAgent


class FakeSource:
    def search(self, topic):
        return ["Software engineering", "Unavailable"]

    def read(self, title):
        if title == "Unavailable":
            raise ResearchError("Article unavailable")
        return Article(title, "Software engineering is an engineering approach to software. "
                       "It includes design, testing, and maintenance.", "https://example.org/software")


class AgentTests(unittest.TestCase):
    def test_loop_produces_cited_answer_and_recovers_from_one_failed_read(self):
        trace = []
        answer = TopicAgent(FakeSource(), trace.append).explain("software engineering")
        self.assertIn("design, testing, and maintenance", answer)
        self.assertIn("[1] Software engineering: https://example.org/software", answer)
        self.assertTrue(any("Article unavailable" in line for line in trace))
        self.assertEqual([line.split(":", 1)[0] for line in trace],
                         ["THINK", "ACT", "OBSERVE"] * 4)

    def test_empty_topic_is_rejected_before_network(self):
        with self.assertRaises(ValueError):
            TopicAgent(FakeSource()).explain("  ")

    def test_no_results_does_not_invent_an_answer(self):
        class Empty(FakeSource):
            def search(self, topic):
                return []
        with self.assertRaises(ResearchError):
            TopicAgent(Empty(), lambda _: None).explain("unknown")

    def test_all_failed_reads_do_not_invent_an_answer(self):
        class Failed(FakeSource):
            def read(self, title):
                raise ResearchError("offline")
        with self.assertRaises(ResearchError):
            TopicAgent(Failed(), lambda _: None).explain("software")


if __name__ == "__main__":
    unittest.main()
