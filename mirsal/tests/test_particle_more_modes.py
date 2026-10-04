"""Add-more source switches and quotes over HTTP; provider and jobs are fakes."""
import unittest
from unittest import mock

from mirsal.flow import particle_sets as ps
from mirsal.generation import higgsfield
from tests.test_effects_api import EffectsApiTests


class ParticleMoreModes(unittest.TestCase):
    setUpClass = classmethod(EffectsApiTests.setUpClass.__func__)
    tearDownClass = classmethod(EffectsApiTests.tearDownClass.__func__)
    req = EffectsApiTests.req
    def empty_set(self, kind='drawn'):
        return ps.create(self.c.out, self.c.lib, owners=[self.sid], elements=['stars'], kind=kind)

    def test_image_set_can_quote_kling_without_a_previous_video_run(self):
        s = self.empty_set()
        before = len([c for c in self.cli.calls if c[:2] == ['generate', 'create']])
        status, quote = self.req('POST', f"/api/particles/{s['id']}/more", {'mode':'video', 'grid':'2x2', 'elements':['stars'], 'estimate':True})
        self.assertEqual((status, quote['credits'], quote['grid']), (200, 4.5, [2, 2]))
        self.assertTrue(quote['effect'].startswith('E'))
        self.assertEqual(before, len([c for c in self.cli.calls if c[:2] == ['generate', 'create']]))
        self.assertEqual(ps.view(self.c.out, self.c.lib, s['id'])['n_cells'], 0)

    def test_video_origin_can_quote_an_image_sheet_explicitly(self):
        s = self.empty_set('video')
        status, quote = self.req('POST', f"/api/particles/{s['id']}/more", {'mode':'drawn', 'elements':['stars'], 'estimate':True})
        self.assertEqual(status, 200)
        self.assertEqual((quote['kind'], quote['n']), ('particles', 4))

    def test_unknown_price_prevents_sheet_job_even_with_go(self):
        s = self.empty_set()
        before = len([c for c in self.cli.calls if c[:2] == ['generate', 'create']])
        with mock.patch.object(higgsfield, 'cost', side_effect=higgsfield.HiggsError('fake quote failure')):
            status, body = self.req('POST', f"/api/particles/{s['id']}/more", {'mode':'drawn', 'elements':['stars'], 'go':True})
        self.assertEqual(status, 409)
        self.assertIn('price is unavailable', body['error'])
        self.assertEqual(before, len([c for c in self.cli.calls if c[:2] == ['generate', 'create']]))

    def test_unknown_price_prevents_kling_job_even_with_go(self):
        s = self.empty_set()
        before = len([c for c in self.cli.calls if c[:2] == ['generate', 'create']])
        with mock.patch.object(higgsfield, 'cost', side_effect=higgsfield.HiggsError('fake quote failure')):
            status, body = self.req('POST', f"/api/particles/{s['id']}/more", {'mode':'video', 'go':True})
        self.assertEqual(status, 409)
        self.assertIn('price is unavailable', body['error'])
        self.assertEqual(before, len([c for c in self.cli.calls if c[:2] == ['generate', 'create']]))


if __name__ == '__main__':
    unittest.main()
