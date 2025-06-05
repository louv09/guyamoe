from django.test import TestCase
import random
from api.views import sort_naturally_input_filenames


class InputFilenameTestCase(TestCase):
    def setUp(self):
        pass

    def shuffle_and_compare(self, filenames):
        shuffled_filenames = random.sample(filenames, len(filenames))  # shuffled but not inplace
        self.assertEqual(sort_naturally_input_filenames(shuffled_filenames), filenames)

    def test_basic_non_zeropad(self):
        self.shuffle_and_compare(['1.png', '2.png', '10.png', '11.png', '20.png', '21.png'])

    def test_basic_zeropad(self):
        self.shuffle_and_compare(['01.png', '02.png', '10.png', '11.png', '20.png', '21.png'])

    def test_basic_zeropad_non_zeropad_point(self):
        self.shuffle_and_compare(['01.png', '01.1.png', '01.11.png', '02.png', '10.png', '10.1.png', '11.png', '20.png', '21.png'])

    def test_basic_zeropad_zeropad_point(self):
        self.shuffle_and_compare(['01.png', '01.01.png', '01.11.png', '02.png', '10.png', '10.01.png', '11.png', '20.png', '21.png'])

    def test_basic_non_zeropad_mix_zeropad_point(self):
        self.shuffle_and_compare(['1.png', '1.01.png', '1.1.png', '1.11.png'])

    def test_basic_text_split_non_zeropad_non_zeropad_point(self):
        self.shuffle_and_compare(['1.png', '1p1.png', '1p10.png', '1p11.png'])

    def test_basic_prefix_text_split_non_zeropad_non_zeropad_point(self):
        self.shuffle_and_compare(['ch1_1.png', 'ch1_1p1.png', 'ch1_1p10.png', 'ch1_1p11.png', 'ch2_1.png'])

    def test_check_numbered_are_not_intepreted_as_negative(self):
        self.shuffle_and_compare(['ch-1.01.png', 'ch-1.1.png', 'ch-1.2.png', 'ch-1.2.png'])

    def test_twitter_upload_without_renaming(self):
        self.shuffle_and_compare([
            "renrenmacchiato-1433015388736921602-20210901_053427-img1.jpg",
            "renrenmacchiato-1433015388736921602-20210901_053427-img2.jpg",
            "renrenmacchiato-1433015388736921602-20210901_053427-img3.jpg",
            "renrenmacchiato-1433015388736921602-20210901_053427-img4.jpg",
            "renrenmacchiato-1433015401684746247-20210901_053430-img1.jpg",
            "renrenmacchiato-1433015401684746247-20210901_053430-img2.jpg",
            "renrenmacchiato-1433015401684746247-20210901_053430-img3.jpg",
            "renrenmacchiato-1433015401684746247-20210901_053430-img4.jpg",
            "renrenmacchiato-1433015414301204487-20210901_053433-img1.jpg",
            "renrenmacchiato-1433015414301204487-20210901_053433-img2.jpg",
            "renrenmacchiato-1433015414301204487-20210901_053433-img3.jpg",
            "renrenmacchiato-1433015414301204487-20210901_053433-img4.jpg",
            "renrenmacchiato-1433015425982361600-20210901_053436-img1.jpg",
            "renrenmacchiato-1433015425982361600-20210901_053436-img2.jpg",
        ])
