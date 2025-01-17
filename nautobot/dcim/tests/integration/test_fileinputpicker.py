from django.urls import reverse

from nautobot.core.testing.integration import SeleniumTestCase, WebDriverWait


class ClearableFileInputTestCase(SeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.user.is_superuser = True
        self.user.save()
        self.login(self.user.username, self.password)

    def tearDown(self):
        self.logout()
        super().tearDown()

    def test_clearable_file_input(self):
        """
        Ensure clearable input file type has working clear and info display.
        """
        # Visit the Add device type page
        self.browser.visit(f"{self.live_server_url}{reverse('dcim:devicetype_add')}")
        WebDriverWait(self.browser, 10).until(lambda driver: driver.is_text_present("Add a new device type"))

        # Find the first file input button and scroll to it
        front_image_button = self.browser.find_by_css("span.group-span-filestyle.input-group-btn").first
        front_image_button.scroll_to()

        # cancel button is NOT visible initially
        self.assertFalse(self.browser.find_by_css("button.clear-button").first.visible)

        # Test file text changes after selecting a file
        file_selection_indicator_css = "div.bootstrap-filestyle input[type='text'].form-control"
        self.assertEqual(self.browser.find_by_css(file_selection_indicator_css).first.value, "")
        front_image_file_input = self.browser.find_by_id("id_front_image").first
        front_image_file_input.value = "/dev/null"
        self.assertEqual(self.browser.find_by_css(file_selection_indicator_css).first.value, "null")

        # clear button is now visible
        clear_button = self.browser.find_by_css("button.clear-button").first
        self.assertTrue(clear_button.visible)

        # clicking clearbutton should hide the button, and wipe the file input value
        clear_button.click()
        self.assertFalse(clear_button.visible)
        self.assertEqual(front_image_file_input.value, "")
