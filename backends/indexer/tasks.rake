
require "pathname"

namespace :gen do
  desc "Generate index of the database"
  task :index do
    index_path = Pathname.new("#{$root}/gen/indexer/index-unified.json")
    Dir.chdir "#{$root}/backends/indexer" do
      FileUtils.mkdir_p index_path.dirname
      require "open3"
      stdout, _stderr, _status = Open3.capture3("node", "index-unifieddb.js", $root.to_s)
      File.write index_path, stdout
    end
  end
end
