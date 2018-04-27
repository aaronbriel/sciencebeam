from importlib import import_module

import logging

from sciencebeam.utils.config import parse_list

from sciencebeam.pipelines import ChainedPipeline

LOGGER = logging.getLogger(__name__)

class UnsupportedDataTypeError(AssertionError):
  def __init__(self, data_type):
    self.data_type = data_type
    super(UnsupportedDataTypeError, self).__init__('Unsupported data type %s' % data_type)

class SimplePipelineRunner(object):
  def __init__(self, steps):
    # type: (List[PipelineStep])
    LOGGER.debug('creating pipeline with steps: %s', steps)
    self._steps = steps

  def get_supported_types(self):
    return {
      data_type
      for step in self._steps
      for data_type in step.get_supported_types()
    }

  def convert(self, content, filename, data_type):
    # type: (str, str, str) -> dict
    current_item = {
      'content': content,
      'filename': filename,
      'type': data_type
    }
    num_processed = 0
    for step in self._steps:
      data_type = current_item['type']
      if data_type not in step.get_supported_types():
        LOGGER.debug('skipping step (type "%s" not supported): %s', data_type, step)
        continue
      LOGGER.debug('executing step (with type "%s"): %s', data_type, step)
      current_item = step(current_item)
      num_processed += 1
    if not num_processed:
      raise UnsupportedDataTypeError(data_type)
    return current_item

def create_simple_pipeline_runner_from_pipeline(pipeline, config, args):
  return SimplePipelineRunner(pipeline.get_steps(config, args))

def _pipeline(config):
  # type: (dict) -> Pipeline
  pipeline_module_names = parse_list(config.get(u'pipelines', u'default'))
  pipeline_modules = [
    import_module(pipeline_module_name)
    for pipeline_module_name in pipeline_module_names
  ]
  pipelines = [pipeline_module.PIPELINE for pipeline_module in pipeline_modules]
  return ChainedPipeline(pipelines)

def add_arguments(parser, config, argv=None):
  pipeline = _pipeline(config)
  pipeline.add_arguments(parser, config, argv=argv)

def create_simple_pipeline_runner_from_config(config, args):
  pipeline = _pipeline(config)
  return create_simple_pipeline_runner_from_pipeline(pipeline, config, args)