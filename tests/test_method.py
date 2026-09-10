from fractions import Fraction
import math
import random
import unittest

from risk_controlled_segmentation.method import (
    aggregate_image_losses, calibrate_aggregate, image_omission, nested_region, quantized_omission,
)


class MethodTests(unittest.TestCase):
    def test_boundary_equality_and_one_quantum(self):
        # At n=20 and alpha=.05 the allowable total is exactly .05.
        answer=calibrate_aggregate([2500,0],loss_denominator=50000,n_images=20,grid_denominator=1,alpha='1/20')
        self.assertTrue(answer.certified); self.assertEqual(answer.lambda_index,0)
        answer=calibrate_aggregate([2501,0],loss_denominator=50000,n_images=20,grid_denominator=1,alpha='1/20')
        self.assertEqual(answer.lambda_index,1)

    def test_fallback_distinct_from_admissible_endpoint(self):
        a=calibrate_aggregate([1,0],loss_denominator=1,n_images=1,grid_denominator=1,alpha='1/20')
        b=calibrate_aggregate([1,0],loss_denominator=1,n_images=19,grid_denominator=1,alpha='1/20')
        self.assertFalse(a.certified); self.assertEqual(a.as_dict()['fallback'],'ALL_OMEGA')
        self.assertTrue(b.certified); self.assertEqual(b.as_dict()['fallback'],'NONE')
        self.assertEqual(a.total_loss,b.total_loss)

    def test_quantization_10000_independent_cases(self):
        rng=random.Random(1729)
        for _ in range(10000):
            area=rng.randint(1,10**9); missed=rng.randint(0,area)
            raw=Fraction(missed,area); expected=Fraction(math.ceil(raw*10000),10000)
            observed=quantized_omission(missed,area)
            self.assertEqual(observed,expected)
            self.assertGreaterEqual(observed,raw); self.assertLess(observed-raw,Fraction(1,10000))

    def test_image_equal_expert_weights_not_pooled_pixels(self):
        raw,q=image_omission([(1,1),(0,100),(0,100),(0,100),(0,100)],expected_experts=5)
        self.assertEqual(raw,Fraction(1,5)); self.assertEqual(q,raw)
        with self.assertRaises(ValueError): image_omission([(1,1)],expected_experts=5)

    def test_padding_inclusive_threshold_and_nested_regions(self):
        scores=[Fraction(1),Fraction(1,2),Fraction(0),Fraction(1)]
        valid=[True,True,True,False]
        self.assertEqual(nested_region(scores,valid,lambda_value=Fraction(1,2)),(True,True,False,False))
        self.assertEqual(nested_region(scores,valid,lambda_value=Fraction(1)),tuple(valid))
        self.assertEqual(nested_region(scores,valid,lambda_value=Fraction(0)),(True,False,False,False))

    def test_aggregate_cannot_detect_cross_image_nonmonotonicity(self):
        rows=[[10,0,0],[0,5,0]]
        with self.assertRaises(ValueError): aggregate_image_losses(rows,loss_denominator=10,grid_denominator=2)
        # Aggregate decline alone is insufficient to validate the per-image assumption.
        result=calibrate_aggregate([10,5,0],loss_denominator=10,n_images=2,grid_denominator=2,alpha='1/2')
        self.assertEqual(result.lambda_index,1)

    def test_exact_oracle_1000_curves(self):
        rng=random.Random(42)
        for _ in range(1000):
            n=rng.randint(1,30); grid=rng.randint(1,10); den=rng.choice([7,50000,10**18+3])
            rows=[]
            for _ in range(n):
                row=[rng.randrange(den+1)]
                for _ in range(grid-1):row.append(rng.randrange(row[-1]+1))
                row.append(0); rows.append(row)
            alpha=rng.choice([Fraction(1,100),Fraction(1,20),Fraction(1,2),Fraction(9,10)])
            totals=aggregate_image_losses(rows,loss_denominator=den,grid_denominator=grid)
            states=[(sum((Fraction(row[i],den) for row in rows),Fraction())+1)/(n+1) for i in range(grid+1)]
            admissible=[i for i,risk in enumerate(states) if risk<=alpha]
            observed=calibrate_aggregate(totals,loss_denominator=den,n_images=n,grid_denominator=grid,alpha=alpha)
            self.assertEqual(observed.lambda_index,min(admissible) if admissible else grid)
            self.assertEqual(observed.certified,bool(admissible))
            self.assertEqual(Fraction(observed.as_dict()['adjusted_risk']),states[observed.lambda_index])

    def test_invalid_inputs_fail(self):
        for curve in ([],[1],[1,2,0],[1,0,1],[-1,0,0],[True,0,0],[1.0,0,0],[11,0,0]):
            with self.subTest(curve=curve),self.assertRaises(ValueError):
                calibrate_aggregate(curve,loss_denominator=10,n_images=1,grid_denominator=2,alpha='1/2')
        for alpha in ('0','1','-1/2','1/0','nan',.05,True):
            with self.subTest(alpha=alpha),self.assertRaises(ValueError):
                calibrate_aggregate([1,0],loss_denominator=1,n_images=20,grid_denominator=1,alpha=alpha)
        for missed,area in ((-1,2),(3,2),(0,0),(True,2),(1,1.5)):
            with self.assertRaises(ValueError):quantized_omission(missed,area)


if __name__=='__main__': unittest.main()
