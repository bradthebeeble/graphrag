import unittest
from graphrag.chat.prompt_templates import get_prompt_template

class TestDistributionTemplate(unittest.TestCase):
    def test_query_without_distribution_values(self):
        query = "show distribution of sales unit over all 24 months"
        template = get_prompt_template("distribution", {
            "query": query,
        })
        print(result)
        self.assertIsInstance(result, str)
        self.assertIn("sales unit", result)
        self.assertIn("24 months", result)
        self.assertIn("Based on the available data", result)

    def test_query_with_distribution_values(self):
        query = "show customer overall rating over the year"
        distribution_values = ["Jan24", "Feb24", "Mar24", "Apr24", "May24", "Jun24", 
   "Jul24", "Aug24", "Sep24", "Oct24", "Nov24", "Dec24"]
        template = get_prompt_template("distribution", {
            "query": query,
            "distribution_values": distribution_values # convert distribution_values into a strigified json AI!
        })
        result = template.format()
        print(result)
        self.assertIsInstance(result, str)
        self.assertIn("customer overall rating", result)
        self.assertIn("year", result)
        self.assertIn(str(distribution_values[0]), result)

if __name__ == "__main__":
    unittest.main()
