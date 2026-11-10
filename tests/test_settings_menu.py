import unittest

from settings_menu import SettingsMenu, SETTINGS_BUTTON, CLOSE_BUTTON, FULLSCREEN_BUTTON, RETURN_BUTTON


def center(rect):
    return rect.left + rect.width / 2, rect.bottom + rect.height / 2


class SettingsMenuTests(unittest.TestCase):
    def test_open_close_and_return(self):
        for close in (CLOSE_BUTTON, RETURN_BUTTON):
            menu = SettingsMenu()
            self.assertEqual(menu.click(center(SETTINGS_BUTTON)), 'consumed')
            self.assertTrue(menu.is_open)
            menu.click(center(close))
            self.assertFalse(menu.is_open)

    def test_escape_closes_menu_then_exits(self):
        menu = SettingsMenu()
        menu.click(center(SETTINGS_BUTTON))
        self.assertEqual(menu.key('escape'), 'consumed')
        self.assertFalse(menu.is_open)
        self.assertEqual(menu.key('escape'), 'quit')

    def test_modal_input_never_reaches_gameplay(self):
        menu = SettingsMenu()
        self.assertEqual(menu.key('other'), 'gameplay')
        menu.click(center(SETTINGS_BUTTON))
        self.assertTrue(menu.blocks_gameplay())
        self.assertEqual(menu.key('other'), 'consumed')
        self.assertEqual(menu.click((0, 0)), 'consumed')
        self.assertEqual(menu.click(None), 'consumed')
        self.assertTrue(menu.is_open)

    def test_f11_and_button_return_identical_action(self):
        menu = SettingsMenu()
        self.assertEqual(menu.key('f11'), 'toggle_fullscreen')
        menu.is_open = True
        self.assertEqual(menu.click(center(FULLSCREEN_BUTTON)), menu.key('f11'))
        self.assertTrue(menu.is_open)

    def test_button_half_open_edges(self):
        r = SETTINGS_BUTTON
        self.assertTrue(r.contains((r.left, r.bottom)))
        self.assertFalse(r.contains((r.left + r.width, r.bottom)))
        self.assertFalse(r.contains((r.left, r.bottom + r.height)))
        self.assertFalse(r.contains(None))
