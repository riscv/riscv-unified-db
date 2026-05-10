# Copyright (c) Ventana Micro Systems
# SPDX-License-Identifier: BSD-3-Clause-Clear

namespace :chore do

  desc "Update golden profile_extensions output"
  task :update_golden_profile_extensions do
    Rake::Task["gen:resolved_arch"].invoke
    sh "uv run #{$root}/tools/python/profile_extensions.py #{$root}/gen/resolved_spec/_ > #{$root}/tests/golden/profile_extensions.golden"
  end

  desc "Update golden encode/decode failures output"
  task :update_golden_encode_decode do
    Rake::Task["gen:resolved_arch"].invoke
    sh "uv run #{$root}/tools/python/test_encode_decode.py --spec #{$root}/gen/resolved_spec/_ --only-ko > #{$root}/tools/python/encode_decode.golden; true"
  end

end

namespace :test do

  desc "Test that generated profile_extensions matched golden version"
  task :profile_extensions do
    Rake::Task["gen:resolved_arch"].invoke

    $logger.info "Testing profile_extensions"
    sh "uv run #{$root}/tools/python/profile_extensions.py #{$root}/gen/resolved_spec/_ > test-profile_extensions.txt"
    sh "diff -u #{$root}/tests/golden/profile_extensions.golden test-profile_extensions.txt" do |ok, res|

      rm "test-profile_extensions.txt", :force => true, :verbose => false
      if ok
        puts "PASSED"
      else
        warn <<~MSG

          The list of extensions associated with profiles has changed.

          If this is expected, run:
          ./do chore:update_golden_profile_extensions
          git add tests/golden/profile_extensions.golden

          And commit.
        MSG
        exit 1
      end
    end
  end

  desc "Test that generated encode/decode failures output matches golden version"
  task :encode_decode do
    Rake::Task["gen:resolved_arch"].invoke

    $logger.info "Testing encode/decode failures output"
    sh "uv run #{$root}/tools/python/test_encode_decode.py --spec #{$root}/gen/resolved_spec/_ --only-ko > test-encode_decode.txt; true"
    sh "diff -u #{$root}/tools/python/encode_decode.golden test-encode_decode.txt" do |ok, res|

      rm "test-encode_decode.txt", :force => true, :verbose => false
      if ok
        puts "PASSED"
      else
        warn <<~MSG

          The encode/decode failures output has changed.

          If this is expected, run:
          ./do chore:update_golden_encode_decode
          git add tools/python/encode_decode.golden

          And commit.
        MSG
        exit 1
      end
    end
  end
end
