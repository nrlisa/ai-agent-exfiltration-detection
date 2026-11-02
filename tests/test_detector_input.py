import unittest

from src.evidence.detector_input import to_detector_input


class DetectorInputTests(unittest.TestCase):
    def test_complete_event(self):
        event = {
            "eventTime": "2026-10-27T10:06:26Z",
            "eventName": "GetObject",
            "requestParameters": {
                "bucketName": "fyp-experiment-data",
                "key": "synthetic/experiment-test-data.txt",
            },
            "userIdentity": {
                "arn": "arn:aws:iam::000000000000:root",
            },
            "sourceIPAddress": "172.17.0.1",
            "additionalEventData": {
                "bytesTransferredOut": 75,
            },
            "errorCode": None,
        }

        result = to_detector_input(event)

        self.assertEqual(result["action"], "GetObject")
        self.assertEqual(result["bucket"], "fyp-experiment-data")
        self.assertEqual(result["bytes_transferred_out"], 75)
        self.assertIsNone(result["error_code"])

    def test_degraded_event(self):
        event = {
            "eventTime": "2026-10-27T10:06:00Z",
            "eventName": "GetObject",
            "requestParameters": {
                "key": "synthetic/experiment-test-data.txt",
            },
            "userIdentity": {"arn": "MASKED"},
            "sourceIPAddress": "172.17.0.1",
            "additionalEventData": {
                "bytesTransferredOut": 75,
            },
        }

        result = to_detector_input(event)

        self.assertIsNone(result["bucket"])
        self.assertEqual(result["identity"], "MASKED")
        self.assertEqual(result["bytes_transferred_out"], 75)


if __name__ == "__main__":
    unittest.main()