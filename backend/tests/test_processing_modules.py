from django.test import TestCase
from apps.processing.parser import SheetParserService, MarkdownSheetParser
from apps.processing.validation import ValidationService
from apps.processing.analysis import AnalysisEngineService
from apps.processing.ranking import RankingEngineService
from apps.processing.comparison import ComparisonEngineService

class ProcessingModulesStructureTests(TestCase):
    def test_all_modules_instantiate(self):
        parser_service = SheetParserService()
        md_parser = MarkdownSheetParser()
        val_service = ValidationService()
        analysis_service = AnalysisEngineService()
        ranking_service = RankingEngineService()
        comp_service = ComparisonEngineService()

        self.assertIsNotNone(parser_service)
        self.assertIsNotNone(md_parser)
        self.assertIsNotNone(val_service)
        self.assertIsNotNone(analysis_service)
        self.assertIsNotNone(ranking_service)
        self.assertIsNotNone(comp_service)

    def test_analysis_and_ranking_service_methods(self):
        analysis_service = AnalysisEngineService()
        stats = analysis_service.calculate_cohort_statistics([], [])
        self.assertIn("summary_metrics", stats)
        self.assertIn("gpa_distribution_histogram", stats)

        ranking_service = RankingEngineService()
        ranked = ranking_service.calculate_ranks([])
        self.assertEqual(ranked, [])
